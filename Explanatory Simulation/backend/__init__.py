"""Local, loopback-only teaching bridge for the GRAD simulator."""

# The plant the lab teaches and simulates, by the name engines.get takes: the
# B58 in the 2023 GR Supra (20 October 2026, the four-engine build). Named once,
# here, so the simulator (simulation.py, server.py) and the vehicle card
# (catalog.py) cannot describe two engines. There is no default engine
# (CLAUDE.md mistake 1).
LAB_PLANT = "b58"
