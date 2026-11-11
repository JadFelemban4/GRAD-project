# The Anatomy drawing kit (vendored)

`iso-kit.mjs` is copied unchanged from the Anatomy skill,
https://github.com/wheresryan22/anatomy, commit `1482e8469b0a9e0d8cc18ea2740a01423d29ae80`
(18 October 2026), file `kit/iso-kit.mjs`, SHA-1 `46c0b262a4941533800474cccfa1c347ebf5b7f5` (with LF line ends, as git
stores it; a Windows checkout may write CRLF).
It is MIT-licensed; the licence is `LICENSE` beside it.

It is plain geometry and SVG strings: no network, no file access, no dependencies.
The figures in `../` import it at build time and inline it into their pages, so
the built pages need nothing else.

Do not edit it here. To take a newer version, copy the file again, record the new
commit and SHA-1 above, rebuild every figure (`npm run figures`) and look at them.
