#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

files = os.listdir("source/_posts")
for f in files:
    if "2012-09-07" in f and "arch" in f:
        print("Filename:", f)
        print(f"Length: {len(f)}")
        b = f.encode("utf-8")
        print("Hex first 20 bytes:", b[:20].hex())
        for i in range(min(len(f), 20)):
            ch = f[i]
            byte_val = b[i]
            print(
                f"Pos {i}: {repr(ch)} Byte: {byte_val:02x}({chr(byte_val) if byte_val < 128 else 'N/A'})"
            )
