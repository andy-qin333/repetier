



#include "AT24CXXX.h"



AT24CXXX::AT24CXXX() {
}

void AT24CXXX::Memory_Size( int size )
{
	memory_size = size;
}

void AT24CXXX::WriteByte( int DeviceAddress, int DataAddress, uint8_t Data )
{
  int error=0;
	int rData = Data;
	Wire.beginTransmission(DeviceAddress);
	if( memory_size > 3 )
	{
		Wire.write( (DataAddress & 0xff00) >> 8 );
	}
	Wire.write(DataAddress & 0x00ff);
	Wire.write(rData);
	Wire.endTransmission();
  error=Wire.endTransmission();
 // Serial.println(error);delay(1000);
	delay(10);
}

byte AT24CXXX::ReadByte( int DeviceAddress, int DataAddress )
{
   uint8_t data = 0xFF;
	Wire.beginTransmission(DeviceAddress);
	if( memory_size > 3 )
	{
		Wire.write( (DataAddress & 0xff00) >> 8 );
	}
	Wire.write(DataAddress & 0x00ff);
	Wire.endTransmission();
	Wire.requestFrom(DeviceAddress, 1);
	delay(10);

	if (Wire.available())
	{
		data = Wire.read();
	}
	delay(10);
	return data;
}


void AT24CXXX::WriteBuffer( int DeviceAddress, int DataAddress, byte *buffer, unsigned int offset, unsigned int count )
{
	byte * p = buffer + offset;
	for( int idx = 0; idx < count;  p++,idx++ )
	{
		WriteByte( DeviceAddress, DataAddress + idx, *p );
	}
		
}

byte* AT24CXXX::ReadBuffer( int DeviceAddress, int DataAddress, byte *buffer, unsigned int count )
{
	byte *p = buffer;
	int idx = 0;

	for(idx = 0;idx < count; p++, idx++)
	{
		*p = ReadByte(DeviceAddress, DataAddress + idx);
	}
		
	return p;
}


void AT24CXXX::WriteString( int DeviceAddress, byte DataAddress, String str )
{
	int n = str.length();	//锟街凤拷锟斤拷锟斤拷锟斤拷
	byte data[n];
	for(int i=0; i<n; i++)
	{
		data[i] = str.charAt(i);	//锟斤拷取锟斤拷 i+1 锟斤拷锟街凤拷
	}
	WriteBuffer( DeviceAddress, DataAddress, data, 0, n);
}

String AT24CXXX::ReadString( int DeviceAddress, byte DataAddress,unsigned int count )
{
	String data="";
	int idx;
	for( idx = 0; idx < count; idx++ )
	{
		data += char( ReadByte( DeviceAddress, DataAddress + idx ) );
	}	
	
	return data;
}

