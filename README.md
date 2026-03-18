### **DOCS:**
https://adamz389.github.io/pfw/

## Install `mpremote`

Open your command prompt (CMD) and run:

```bash
pip install --user mpremote
```

##  2. Test if it works
```bash
mpremote --help
```
### for unrecognized error:
```bash
enter PATH env var and put:
C:\Users\<user>\AppData\Roaming\Python\<Python314>\Scripts
```

## 3. Connect
```bash
mpremote connect auto
```
### if that doesnt work:
```bash
mpremote connect <COM> (replace COM with board number like COM5)
```

## 4. Install package
```bash
mpremote mip install github:adamz389/conn
```

## 5. Test using REPL
```bash
mpremote connect <COM>

import fmw
fmw.Utils.Clamp(15, 0, 10)
>> 10
```
