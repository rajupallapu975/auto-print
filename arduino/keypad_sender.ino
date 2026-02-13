/*
 * Arduino Uno Keypad Sender
 * Connects a 4x4 Matrix Keypad to Uno and sends numeric presses to Raspberry Pi via Serial.
 * 
 * Requirements: Install "Keypad" library by Mark Stanley, Alexander Brevig
 */

#include <Keypad.h>

const byte ROWS = 4; // four rows
const byte COLS = 4; // four columns

// Define the Keymap
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};

// Connect keypad R1, R2, R3, R4 to these Arduino pins
byte rowPins[ROWS] = {9, 8, 7, 6}; 
// Connect keypad C1, C2, C3, C4 to these Arduino pins
byte colPins[COLS] = {5, 4, 3, 2}; 

// Create the Keypad
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

void setup() {
  Serial.begin(9600); // Same baud rate as Raspberry Pi
}

void loop() {
  char key = keypad.getKey();

  if (key) {
    // Send all numeric and alphabet keys (A-D, 0-9)
    if ((key >= '0' && key <= '9') || (key >= 'A' && key <= 'D')) {
      Serial.println(key); 
    }
    // Use '#' as Clear
    else if (key == '#') {
      Serial.println("CLEAR");
    }
    // Use '*' as Backspace
    else if (key == '*') {
      Serial.println("BACKSPACE");
    }
  }
}
