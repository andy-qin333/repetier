#include <Arduino.h>
#include "HX711.h"

HX711::HX711(byte tx1_sck, byte rx1_dout, byte amp = 128, double co = 1) {
    TX1_SCK = tx1_sck;
    RX1_DOUT = rx1_dout;
    set_amp(amp);
    COEFFICIENT = co;
    pinMode(TX1_SCK, OUTPUT);
    pinMode(RX1_DOUT, INPUT);
    digitalWrite(TX1_SCK, LOW);
    read();
}

void HX711::set_amp(byte amp) {
    switch (amp) {
        case 32: AMP = 2; break;
        case 64: AMP = 3; break;
        case 128: AMP = 1; break;
    }
}

bool HX711::is_ready() {
    return digitalRead(RX1_DOUT) == LOW;
}

long HX711::read() {
    long val = 0;
    while (!is_ready());
    for (int i = 0; i < 24; i++) {
        pulse(TX1_SCK);
        val <<= 1;
        if (digitalRead(RX1_DOUT) == HIGH) val++;
    }
    for (int i = 0; i < AMP; i++) {
        pulse(TX1_SCK);
    }
    return val & (1L << 23) ? val | ((-1L) << 24) : val;
}

double HX711::bias_read() {
    return (read() - OFFSET) * COEFFICIENT;
}

double HX711::tare(int t) {
    double sum = 0;
    for (int i = 0; i < t; i++) {
        sum += read();
    }
    set_offset(sum / t);
	return sum / t;
}

void HX711::set_offset(long offset) {
    OFFSET = offset;
}

void HX711::set_co(double co) {
    COEFFICIENT = co;
}

