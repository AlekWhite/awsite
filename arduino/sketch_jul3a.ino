#include "DHT.h"
#include <Arduino.h>
#define DHTTYPE DHT11
#define DHTPIN 7 
#define REDPIN 9
#define GREENPIN 6
#define BLUEPIN 5



DHT dht(DHTPIN, DHTTYPE);


float oneHourData[60] = {};
float twelveHourData[12] = {};

int counter = 0;
float temp = 0;
float oneHourAvg = 0;

// setup
void setup() {
  
  Serial.begin(9600);
  Serial.setTimeout(1);
  Serial.println(F("DHTxx test!"));
  dht.begin();

  for (int i=0; i<12; i++){
    twelveHourData[i] = -99.99;
  }

  pinMode(REDPIN, OUTPUT);
  pinMode(GREENPIN, OUTPUT);
  pinMode(BLUEPIN, OUTPUT);

  analogWrite(REDPIN, 0);
  analogWrite(BLUEPIN, 0);
  analogWrite(GREENPIN, 0);


}

// updates the temp history
void updateArray(float* targetArray, float initalVal, int arraySize){

    float holderArray[arraySize] = {};
    holderArray[0] = initalVal;

    for (int i=0; i<arraySize-1; i++){
      holderArray[i+1] = targetArray[i];}

    for (int i=0; i<arraySize; i++){
      targetArray[i] = holderArray[i];}

}

// get temp data (C)
float getTemp(){
  float t = dht.readTemperature();
  if (isnan(t)) {
    Serial.println(F("Failed to read from DHT sensor!"));
  }
  return t;
}

void updateColor(String input){

  Serial.println(input);

  String number = "";
  int rgb[3] = {};
  int count = 0;
  String digits = "0123456789";

  for (int j=0; j<input.length(); j++){

    if (digits.indexOf(input[j]) != -1 ){
      number += input[j];}

    if ((digits.indexOf(input[j]) == -1 ) || (j == input.length()-1)){
      rgb[count] = number.toInt();
      number = "";
      count ++;}}

  Serial.println(rgb[0]);
  Serial.println(rgb[1]);
  Serial.println(rgb[2]);

  analogWrite(REDPIN, rgb[0]);
  analogWrite(BLUEPIN, rgb[2]);
  analogWrite(GREENPIN, rgb[1]);
}

// main loop
int oldLoopCount = 0;
void loop() {

  // wait until input, or for new tpa data
  int smallCounter = oldLoopCount;
  while((Serial.available() == 0) && (smallCounter < 120)){
    smallCounter ++;
    delay(500);}

  // gets color input
  if (Serial.available() > 0){
    String line = Serial.readString();
    updateColor(line);
    oldLoopCount = smallCounter;
    }

  // gets the temp every minute
  if (smallCounter >= 120){
    oldLoopCount = 0;
    temp = getTemp();
    updateArray(oneHourData, temp, 60);
    oneHourAvg += temp;

    // handles 12-hour data
    if (counter == 60){
      updateArray(twelveHourData, (oneHourAvg / 60), 12);
      oneHourAvg = 0;
      counter = 0;}
    counter ++;

    // prints temp
    Serial.print("# TEMP DATA # ");
    Serial.print(temp);
    Serial.print(" #");

    // prints twelveHourData
    for(int i=0; i<sizeof(twelveHourData)/sizeof(twelveHourData[0]); i++){
      Serial.print(" ");
      Serial.print(twelveHourData[i]);}
    Serial.println();


  }
}