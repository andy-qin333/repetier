M206 P0 T1 F76.1905						;addr:0 type:1(float) 76.1905 X-axis steps/mm
M206 P32 T1 F150.0000               ;addr:32 type:1(float) 150.0000 X-axis max feedrate[mm/s]
M206 P64 T1 F10.0000                ;addr:64 type:1(float) 10.0000 X-axis start feedrate[mm/s]
M206 P96 T1 F500.0000               ;addr:96 type:1(float) 500.0000 X-axis print acceleration[mm/s^2]
M206 P140 T1 F0.0000                ;addr:140 type:1(float) 0.0000 X-axis home pos[mm]
M206 P152 T1 F254.0000              ;addr:152 type:1(float) 230.0000 X-axis max length[mm]
M206 P164 T1 F60.0000               ;addr:164 type:1(float) 60.0000 X-axis homing feedrate[mm/s]
M206 P344 T4 S1                     ;addr:344 type:4(int8) 1 X axis EN_PinInvalid
M206 P345 T4 S0                     ;addr:345 type:4(int8) 0 X axis DIR_PinInvalid
M206 P346 T4 S0                     ;addr:346 type:4(int8) 0 X axis STEP_PinInvalid
M206 P347 T4 S0                     ;addr:347 type:4(int8) 0 X axis InvertDir

M206 P425 T4 S1						;addr:425 type:4(int8) 255 X-axis minimum limit switch invalid state
M206 P426 T4 S1						;addr:426 type:4(int8) 255 X-axis maximum limit switch invalid state
M206 P427 T4 S0						;addr:427 type:4(int8) 255 X-axis limit mode[0-MIN / 1-MAX]

M206 P4 T1 F114.2856                 ;addr:4 type:1(float) 114.2856 Y-axis steps/mm
M206 P36 T1 F150.0000               ;addr:36 type:1(float) 150.0000 Y-axis max feedrate[mm/s]
M206 P68 T1 F10.0000                ;addr:68 type:1(float) 10.0000 Y-axis start feedrate[mm/s]
M206 P100 T1 F500.0000              ;addr:100 type:1(float) 500.0000 Y-axis print acceleration[mm/s^2]
M206 P144 T1 F0.0000                ;addr:144 type:1(float) 0.0000 Y-axis home pos[mm]
M206 P156 T1 F254.0000              ;addr:156 type:1(float) 210.0000 Y-axis max length[mm]
M206 P168 T1 F60.0000               ;addr:168 type:1(float) 60.0000 Y-axis homing feedrate[mm/s]
M206 P348 T4 S1                     ;addr:348 type:4(int8) 1 Y axis EN_PinInvalid
M206 P349 T4 S0                     ;addr:349 type:4(int8) 0 Y axis DIR_PinInvalid
M206 P350 T4 S0                     ;addr:350 type:4(int8) 0 Y axis STEP_PinInvalid
M206 P351 T4 S1                    ;addr:351 type:4(int8) 1 Y axis InvertDir

M206 P428 T4 S1						;addr:428 type:4(int8) 52 Y-axis minimum limit switch invalid state
M206 P429 T4 S1						;addr:429 type:4(int8) 18 Y-axis maximum limit switch invalid state
M206 P430 T4 S0						;addr:430 type:4(int8) 120 Y-axis limit mode[0-MIN / 1-MAX]

M206 P8 T1 F400.0000                ;addr:8 type:1(float) 400.0000 Z-axis steps/mm
M206 P40 T1 F120.0000               ;addr:40 type:1(float) 120.0000 Z-axis max feedrate[mm/s]
M206 P72 T1 F5.0000                 ;addr:72 type:1(float) 5.0000 Z-axis start feedrate[mm/s]
M206 P104 T1 F200.0000              ;addr:104 type:1(float) 200.0000 Z-axis print acceleration[mm/s^2]
M206 P148 T1 F0.0000                ;addr:148 type:1(float) 0.0000 Z-axis home pos[mm]
M206 P160 T1 F210.0000              ;addr:160 type:1(float) 254.0000 Z-axis max length[mm]
M206 P172 T1 F40.0000               ;addr:172 type:1(float) 40.0000 Z-axis homing feedrate[mm/s]
M206 P352 T4 S1                     ;addr:352 type:4(int8) 1 Z axis EN_PinInvalid
M206 P353 T4 S0                     ;addr:353 type:4(int8) 0 Z axis DIR_PinInvalid
M206 P354 T4 S0                     ;addr:354 type:4(int8) 0 Z axis STEP_PinInvalid
M206 P355 T4 S1                     ;addr:355 type:4(int8) 1 Z axis InvertDir-----------

M206 P431 T4 S1						;addr:431 type:4(int8) 86 Z-axis minimum limit switch invalid state
M206 P432 T4 S1						;addr:432 type:4(int8) 255 Z-axis maximum limit switch invalid state
M206 P433 T4 S1						;addr:433 type:4(int8) 255 Z-axis limit mode[0-MIN / 1-MAX]

M206 P12 T1 F149.2710               ;addr:12 type:1(float) 101.8500 Extr.0 steps/mm
M206 P44 T1 F24.0000                ;addr:44 type:1(float) 24.0000 Extr.0 max feedrate[mm/s]
M206 P76 T1 F5.0000                 ;addr:76 type:1(float) 5.0000 Extr.0 start feedrate[mm/s]
M206 P108 T1 F1000.0000             ;addr:108 type:1(float) 1000.0000 Extr.0 print acceleration[mm/s^2]
M206 P176 T1 F4.9                     ;addr:176 type:1(float) 4.9000 Extr.0 coordinate-x[mm]
M206 P180 T1 F1.5                     ;addr:180 type:1(float) 1.5000 Extr.0 coordinate-y[mm]
M206 P184 T1 F0.0000                ;addr:184 type:1(float) 0.0000 Extr.0 coordinate-z[mm]
M206 P356 T4 S1                     ;addr:356 type:4(int8) 1 E0 axis EN_PinInvalid
M206 P357 T4 S0                     ;addr:357 type:4(int8) 0 E0 axis DIR_PinInvalid
M206 P358 T4 S0                     ;addr:358 type:4(int8) 0 E0 axis STEP_PinInvalid
M206 P359 T4 S0                     ;addr:359 type:4(int8) 0 E0 axis InvertDir

M206 P16 T1 F149.271                ;addr:16 type:1(float) 149.2710 Extr.1 steps/mm
M206 P48 T1 F24.0000                ;addr:48 type:1(float) 24.0000 Extr.1 max feedrate[mm/s]
M206 P80 T1 F5.0000                 ;addr:80 type:1(float) 5.0000 Extr.1 start feedrate[mm/s]
M206 P112 T1 F1000.0000             ;addr:112 type:1(float) 1000.0000 Extr.1 print acceleration[mm/s^2]
M206 P188 T1 F45.0000               ;addr:188 type:1(float) 46.0000 Extr.1 coordinate-x[mm]
M206 P192 T1 F1.6000                ;addr:192 type:1(float) 3.5000 Extr.1 coordinate-y[mm]
M206 P196 T1 F0.0000                ;addr:196 type:1(float) 0.0000 Extr.1 coordinate-z[mm]
M206 P360 T4 S1                     ;addr:360 type:4(int8) 1 E1 axis EN_PinInvalid
M206 P361 T4 S0                     ;addr:361 type:4(int8) 0 E1 axis DIR_PinInvalid
M206 P362 T4 S0                     ;addr:362 type:4(int8) 0 E1 axis STEP_PinInvalid
M206 P363 T4 S1                     ;addr:363 type:4(int8) 1 E1 axis InvertDir

M206 P20  T1 F149.271               ;addr:20 type:1(float) 149.2710 Extr.2 steps/mm
M206 P52  T1 F24.0000               ;addr:52 type:1(float) 24.0000 Extr.2 max feedrate[mm/s]
M206 P84  T1 F5.0000                ;addr:84 type:1(float) 5.0000 Extr.2 start feedrate[mm/s]
M206 P116 T1 F1000.0000             ;addr:116 type:1(float) 1000.0000 Extr.2 print acceleration[mm/s^2]
M206 P200 T1 F0.0000                ;addr:200 type:1(float) 0.0000 Extr.2 coordinate-x[mm]
M206 P204 T1 F0.0000                ;addr:204 type:1(float) 0.0000 Extr.2 coordinate-y[mm]
M206 P208 T1 F0.0000                ;addr:208 type:1(float) 0.0000 Extr.2 coordinate-z[mm]
M206 P364 T4 S1                     ;addr:364 type:4(int8) 1 E2 axis EN_PinInvalid
M206 P365 T4 S0                     ;addr:365 type:4(int8) 0 E2 axis DIR_PinInvalid
M206 P366 T4 S0                     ;addr:366 type:4(int8) 0 E2 axis STEP_PinInvalid
M206 P367 T4 S0                     ;addr:367 type:4(int8) 0 E2 axis InvertDir

M206 P24  T1 F149.271               ;addr:24 type:1(float) 149.2710 Extr.3 steps/mm
M206 P56  T1 F24.0000               ;addr:56 type:1(float) 24.0000 Extr.3 max feedrate[mm/s]
M206 P88  T1 F5.0000                ;addr:88 type:1(float) 5.0000 Extr.3 start feedrate[mm/s]
M206 P120 T1 F1000.0000             ;addr:120 type:1(float) 1000.0000 Extr.3 print acceleration[mm/s^2]
M206 P212 T1 F0.0000                ;addr:212 type:1(float) 0.0000 Extr.3 coordinate-x[mm]
M206 P216 T1 F0.0000                ;addr:216 type:1(float) 0.0000 Extr.3 coordinate-y[mm]
M206 P220 T1 F0.0000                ;addr:220 type:1(float) 0.0000 Extr.3 coordinate-z[mm]
M206 P368 T4 S1                     ;addr:368 type:4(int8) 1 E3 axis EN_PinInvalid
M206 P369 T4 S0                     ;addr:369 type:4(int8) 0 E3 axis DIR_PinInvalid
M206 P370 T4 S0                     ;addr:370 type:4(int8) 0 E3 axis STEP_PinInvalid
M206 P371 T4 S0                     ;addr:371 type:4(int8) 0 E3 axis InvertDir

M206 P28  T1 F149.271               
M206 P60  T1 F24.0000               
M206 P92  T1 F5.0000                
M206 P124 T1 F1000.0000             
M206 P224 T1 F0.0000                
M206 P228 T1 F0.0000                
M206 P232 T1 F0.0000                
M206 P372 T4 S0                     
M206 P373 T4 S0                     
M206 P374 T4 S0                     
M206 P375 T4 S0                     

M206 P236 T1 F128.0000               	;addr:236 type:1(float) 115.0000 auto level point.1-x[mm]
M206 P240 T1 F22.0000               	;addr:240 type:1(float) 40.0000 auto level point.1-y[mm]
M206 P244 T1 F210.0000              	;addr:244 type:1(float) 205.0000 auto level point.2-x[mm]
M206 P248 T1 F175.0000               	;addr:248 type:1(float) 188.0000 auto level point.2-y[mm]
M206 P252 T1 F60.0000               	;addr:252 type:1(float) 25.0000 auto level point.3-x[mm]
M206 P256 T1 F175.0000              	;addr:256 type:1(float) 188.0000 auto level point.3-y[mm]
M206 P260 T1 F38.0000               		;addr:260 type:1(float) 0.0000 AutoLevel Sensor pos -x[mm]
M206 P264 T1 F-50.0000                	;addr:264 type:1(float) 32.0000 AutoLevel Sensor pos -y[mm]
M206 P268 T1 F7.0000                	;addr:268 type:1(float) 0.7000 AutoLevel Sensor pos -z[mm]
M206 P272 T1 F5.0000                	;addr:272 type:1(float) 5.0000 AutoLevel check feedrate[mm/s]
M206 P276 T3 S2040               	;addr:276 type:3(int16) 1000 AutoLevel servo open value[600~2400]
M206 P278 T3 S1500               	;addr:278 type:3(int16) 2000 AutoLevel servo close value[600~2400]

;-----------------------------------------------------------------------
; 加热头PID等参数
M206 P280 T1 F10.0000               ;addr:280 type:1(float) 10.0000 Extr.0 heat pid Kp
M206 P284 T1 F0.5000                ;addr:284 type:1(float) 0.5000 Extr.0 heat pid Ki
M206 P288 T1 F30.0000               ;addr:288 type:1(float) 30.0000 Extr.0 heat pid Kd
M206 P292 T4 S255                   ;addr:292 type:4(int8) 255 Extr.0 heat pid Driver Max[0-255]
M206 P293 T4 S0                     ;addr:293 type:4(int8) 0 Extr.0 heat pid Driver Min[0-255]
M206 P384 T1 F280.0000              ;addr:384 type:1(float) 280.0000 Extr.0 max heat temperature
M206 P400 T1 F0.0000                ;addr:400 type:1(float) 0.0000 Extr.0 temperature offset
M206 P420 T4 S0                     ;addr:420 type:4(int8) 0 Extr.0 temperature sensor type[0-NTC3950]

M206 P296 T1 F10.0000               ;addr:296 type:1(float) 10.0000 Extr.1 heat pid Kp
M206 P300 T1 F0.4000                ;addr:300 type:1(float) 0.4000 Extr.1 heat pid Ki
M206 P304 T1 F30.0000               ;addr:304 type:1(float) 30.0000 Extr.1 heat pid Kd
M206 P308 T4 S255                   ;addr:308 type:4(int8) 255 Extr.1 heat pid Driver Max[0-255]
M206 P309 T4 S0                     ;addr:309 type:4(int8) 0 Extr.1 heat pid Driver Min[0-255]
M206 P388 T1 F280.0000              ;addr:388 type:1(float) 280.0000 Extr.1 max heat temperature
M206 P404 T1 F0.0000                ;addr:404 type:1(float) 0.0000 Extr.1 temperature offset
M206 P421 T4 S0                     ;addr:421 type:4(int8) 0 Extr.1 temperature sensor type

M206 P312 T1 F50.0000               ;addr:312 type:1(float) 10.0000 Bed heat pid Kp
M206 P316 T1 F0.9000                ;addr:316 type:1(float) 0.4000 Bed heat pid Ki
M206 P320 T1 F10.0000               ;addr:320 type:1(float) 30.0000 Bed heat pid Kd
M206 P324 T4 S255                   ;addr:324 type:4(int8) 255 Bed heat pid Driver Max[0-255]
M206 P325 T4 S0                     ;addr:325 type:4(int8) 0 Bed heat pid Driver Min[0-255]
M206 P392 T1 F120.0000              ;addr:392 type:1(float) 120.0000 Bed max heat temperature
M206 P408 T1 F0.0000                ;addr:408 type:1(float) 0.0000 Bed temperature offset
M206 P422 T4 S0                     ;addr:422 type:4(int8) 0 Bed temperature sensor type

M206 P328 T1 F50.0000               ;addr:328 type:1(float) 10.0000 Chamber heat pid Kp
M206 P332 T1 F0.5000                ;addr:332 type:1(float) 0.4000 Chamber heat pid Ki
M206 P336 T1 F0.0000               ;addr:336 type:1(float) 30.0000 Chamber heat pid Kd
M206 P340 T4 S255                   ;addr:340 type:4(int8) 255 Chamber heat pid Driver Max[0-255]
M206 P341 T4 S0                     ;addr:341 type:4(int8) 0 Chamber heat pid Driver Min[0-255]
M206 P396 T1 F100                   ;addr:396 type:1(float) 100.0000 Chamber max heat temperature
M206 P412 T1 F0                     ;addr:412 type:1(float) 0.0000 Chamber temperature offset
M206 P423 T4 S0                     ;addr:423 type:4(int8) 0 Chamber temperature sensor type

M206 P416 T1 F0                     ;addr:416 type:1(float) 0.0000 Control board temperature offset
M206 P424 T4 S0                     ;addr:424 type:4(int8) 0 Control board temperature sensor type

;M206 P376 T1 F123678.125            ;addr:376 type:1(float) 276072.2813 Filament printed[mm]
M206 P380 T2 S115200                ;addr:380 type:2(int32) 115200 Baudrate
M206 P436 T2 S1450709556            ;addr:428 type:2(int32) 1450709556 Valid flag value

;V1 K118010001;                      ;更新EEPROM时，请屏蔽序列号，否则会覆盖原有序列号
V3 3DTALK Knight Pro;
V5 V1.00;
