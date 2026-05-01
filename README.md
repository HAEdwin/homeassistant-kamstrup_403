Inspired on https://github.com/golles/ha-kamstrup_403
This version focuses on good, stable operation without any fuss, thus with 40% reduced code

## Features

**Setup & Configuration**
- UI-based setup via Config Flow — no YAML required
- Serial port connection with automatic validation on setup
- Configurable scan interval (60 s – 24 h, default 1 hour)
- Configurable read timeout (0.5 s – 5.0 s)

**Communication**
- Implements the Kamstrup Meter Protocol (KMP) over a serial/IR connection
- Automatic retry on CRC errors (up to 2 retries per read)
- Tolerates up to 2 consecutive complete read failures while keeping entities available with last known values
- Persistent notification after 3 consecutive failures to alert of a real IR connection problem
- Batched register reads (up to 8 registers per request per protocol limit)

**Sensors**
- Heat Energy (E1) — total increasing energy counter
- Cooling Energy (E3) — total increasing energy counter *(disabled by default)*
- Volume — total water volume
- Flow — current flow rate *(disabled by default)*
- Power — current power *(disabled by default)*
- Temp1 / Temp2 / Tempdiff — supply, return, and differential temperatures *(disabled by default)*
- Infoevent & Infoevent counter — meter event monitoring
- Serial number — meter identification
- Hour counter — total operating hours

**Monthly min/max statistics** *(all disabled by default)*
- MinFlow_M / MaxFlow_M with timestamps
- MinPower_M / MaxPower_M with timestamps
- AvgTemp1_M / AvgTemp2_M

**Yearly min/max statistics** *(all disabled by default)*
- MinFlow_Y / MaxFlow_Y with timestamps
- MinPower_Y / MaxPower_Y with timestamps
- AvgTemp1_Y / AvgTemp2_Y

**Home Assistant Integration**
- All sensors use proper device classes, state classes, and units for energy dashboard compatibility
- Date/timestamp sensors decoded from meter date format
- Diagnostics support for troubleshooting via HA diagnostics panel
- Translations: English and Dutch
