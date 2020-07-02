
#ifndef AT24CXXX_h
#define AT24CXXX_h

#if defined(ARDUINO) && ARDUINO >= 100
#include <Arduino.h>
#else
#include "WProgram.h"
#endif

#include <Wire.h>



class AT24CXXX {

	int memory_size;

	public:
		uint8_t Type;
		uint8_t Type1;
	
		
		AT24CXXX();

		void Memory_Size( int size );

		void WriteByte( int DeviceAddress, int DataAddress, uint8_t Data );
		uint8_t ReadByte( int DeviceAddress, int DataAddress );

		void WriteBuffer( int DeviceAddress, int DataAddress, byte *buffer, unsigned int offset, unsigned int count );
		byte* ReadBuffer( int DeviceAddress, int DataAddress, byte *buffer, unsigned int count );

		void WriteString(int DeviceAddress, byte DataAddress, String str);
		String ReadString( int DeviceAddress, byte DataAddress,unsigned int count );		
		
	
	private:
		
		
};
#endif

