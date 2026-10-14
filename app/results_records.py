"""G11: read a bounded local episode extract; no replay/inference is started.

Extract v1 stores provenance, episodes with monotonic recorded time, and
explicit per-channel physical units. Missing channels are never synthesised.
The extract hash identifies the recording; it does not certify current-plant
compatibility. Binary records need a documented extract before this reader.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path

MAX_BYTES=16*1024*1024
MAX_SAMPLES=100_000

def read_episode_panel(root: Path, relative_path: str) -> dict:
    root=Path(root).resolve()
    path=(root/relative_path/'episode_trace.json').resolve()
    panel={'id':'G11','group':'decisions','kind':'line','state':'unavailable',
           'source_files':[f'{relative_path}/episode_trace.json'],'caveats':[],
           'reason':'missing_record','axes':{'x':{'label':'time','unit':'s'},'y':{'label':'value','unit':''}},
           'series':[],'channels':[],'revision':''}
    if not path.is_relative_to(root):
        panel.update(state='withheld',reason='source_outside_project');return panel
    try:
        before=path.stat()
        if before.st_size>MAX_BYTES:raise ValueError('source_too_large')
        raw=path.read_bytes();after=path.stat()
        if (before.st_size,before.st_mtime_ns,before.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):
            raise ValueError('source_updating')
        record=json.loads(raw.decode('utf-8-sig'),parse_constant=lambda _:None)
        if record.get('schema_version')!=1:raise ValueError('episode_schema_missing')
        provenance=record.get('provenance',{})
        if not all(isinstance(provenance.get(k),str) and provenance[k] for k in
                   ('policy','protocol','source_revision','kind','time_unit')):
            raise ValueError('episode_provenance_missing')
        if provenance['kind'] not in ('evaluation','training'):raise ValueError('episode_schema_missing')
        if provenance['time_unit']!='s':raise ValueError('episode_time_invalid')
        index_path=path.parent.parent/'index.json'
        if index_path.is_file():
            if index_path.stat().st_size>MAX_BYTES:raise ValueError('source_too_large')
            index=json.loads(index_path.read_text(encoding='utf-8-sig'))
            policies=index.get('policies',{})
            if provenance['policy'] not in (policies if isinstance(policies,dict) else []):
                raise ValueError('episode_policy_not_in_index')
        # A provenance string is a claim. Compare it with authoritative set
        # sidecars when they exist; otherwise retain the historical extract
        # with an explicit unknown provenance state.
        verified=[]
        summary_path=path.parent/'eval_summary.json'
        if summary_path.is_file():
            if summary_path.stat().st_size>MAX_BYTES:raise ValueError('source_too_large')
            summary=json.loads(summary_path.read_text(encoding='utf-8-sig'))
            if summary.get('policy') and summary['policy']!=provenance['policy']:
                raise ValueError('episode_provenance_mismatch')
            if summary.get('protocol') and summary['protocol']!=provenance['protocol']:
                raise ValueError('episode_provenance_mismatch')
            if summary.get('generation') is not None:
                if summary['generation']!=provenance.get('generation'):
                    raise ValueError('episode_provenance_mismatch')
                verified.append('generation')
            if summary.get('source_revision') is not None:
                if summary['source_revision']!=provenance['source_revision']:
                    raise ValueError('episode_provenance_mismatch')
                verified.append('source_revision')
            if summary.get('policy') or summary.get('protocol'):
                verified.append('policy_protocol')
        config_path=path.parent/'config.json'
        if config_path.is_file():
            if config_path.stat().st_size>MAX_BYTES:raise ValueError('source_too_large')
            config=json.loads(config_path.read_text(encoding='utf-8-sig'))
            generation=config.get('recorded_generation',config.get('generation'))
            if generation is not None:
                if generation!=provenance.get('generation'):
                    raise ValueError('episode_provenance_mismatch')
                verified.append('generation')
        episodes=record.get('episodes')
        if not isinstance(episodes,list) or not episodes or len(episodes)>1000:raise ValueError('episode_schema_missing')
        channel_ids=set();samples=0
        finite=lambda v:isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
        for episode in episodes:
            times=episode.get('time',[]);eid=episode.get('id')
            samples+=len(times)
            if samples>MAX_SAMPLES or not times or not all(finite(t) for t in times) or any(b<=a for a,b in zip(times,times[1:])):
                raise ValueError('episode_time_invalid')
            if not isinstance(eid,(int,str)):raise ValueError('episode_schema_missing')
            channels=episode.get('channels',[])
            if not isinstance(channels,list) or not channels or len(channels)>128:raise ValueError('episode_schema_missing')
            for channel in channels:
                cid=channel.get('id');unit=channel.get('unit');values=channel.get('values')
                if not isinstance(cid,str) or not isinstance(unit,str) or not unit or not isinstance(values,list) or len(values)!=len(times):
                    raise ValueError('episode_channel_invalid')
                if not all(v is None or finite(v) for v in values):raise ValueError('episode_channel_invalid')
                channel_ids.add(cid)
                axis={'x':{'label':'time','unit':'s'},'y':{'label':channel.get('label',cid),'unit':unit}}
                series=[{'id':cid,'label':channel.get('label',cid),'role':'recorded','points':[
                    {'x':t,'y':v,'source_index':i,'episode':eid} for i,(t,v) in enumerate(zip(times,values))]}]
                panel['channels'].append({'id':f'{provenance["policy"]}:{eid}:{cid}',
                    'label':f'{provenance["policy"]} · {eid} · {channel.get("label",cid)}',
                    'unit':unit,'axes':axis,'series':series,'alignment':f'{provenance["source_revision"]}:{eid}'})
        provenance_status='verified' if verified else 'unknown'
        panel.update(state='available',reason=None,revision=hashlib.sha256(raw).hexdigest(),provenance=provenance,
                     provenance_status=provenance_status,verified_provenance_fields=sorted(set(verified)),
                     axes=panel['channels'][0]['axes'],series=panel['channels'][0]['series'])
        panel['caveats']=['recorded_generation_not_current_replay']
        if not verified:panel['caveats'].append('provenance_not_verified_by_sidecar')
        for prefix,code in [('command_','command_channels_missing'),('applied_','applied_channels_missing'),
                            ('obs_','observation_channels_missing'),('reward','reward_channels_missing'),
                            ('torque','torque_channels_missing'),('temp_','thermal_channels_missing'),('event_','event_channels_missing')]:
            if not any(cid.startswith(prefix) for cid in channel_ids):panel['caveats'].append(code)
    except FileNotFoundError:
        pass
    except (OSError,ValueError,TypeError,KeyError,AttributeError) as exc:
        panel['reason']=str(exc) if isinstance(exc,ValueError) and str(exc).startswith(('episode_','source_')) else 'episode_schema_invalid'
    return panel
