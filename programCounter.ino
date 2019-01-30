#define E2_ENABLE 7
#define E1_ENABLE 6
#define BUTTON  5
#define OUTPUT_ENABLE_PIN 4
#define RESET_PIN 3
#define WRITE_PIN 2

int buttonState = 0;
int lastButtonState = 0;
int state = 0;

void setup() {
  pinMode(BUTTON, INPUT);
  pinMode(RESET_PIN, OUTPUT);
  pinMode(OUTPUT_ENABLE_PIN, OUTPUT);
  pinMode(WRITE_PIN, OUTPUT);
  pinMode(E1_ENABLE, OUTPUT);
  pinMode(E2_ENABLE, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  //Serial.println(state);
  if (state == 0){
    Serial.println("Idle...");
    digitalWrite(RESET_PIN, HIGH);
    digitalWrite(OUTPUT_ENABLE_PIN, HIGH);
    digitalWrite(WRITE_PIN, HIGH);
    // E1 is inverted, E2 is not
    digitalWrite(E1_ENABLE, HIGH);
    digitalWrite(E2_ENABLE, LOW);
  } else if (state == 1) {
    Serial.println("Writing...");
    digitalWrite(WRITE_PIN, LOW);
    digitalWrite(OUTPUT_ENABLE_PIN, HIGH);
    digitalWrite(RESET_PIN, LOW);
    digitalWrite(E1_ENABLE, LOW);
    digitalWrite(E2_ENABLE, HIGH);
  } else if (state == 2) {
    Serial.println("Reading...");
    digitalWrite(OUTPUT_ENABLE_PIN, LOW);
    digitalWrite(RESET_PIN, LOW);
    digitalWrite(WRITE_PIN, HIGH);
    digitalWrite(E1_ENABLE, HIGH);
    digitalWrite(E2_ENABLE, LOW);
  }
  buttonState = digitalRead(BUTTON);
  //Serial.println(state);
  if (buttonState != lastButtonState){
    if (buttonState == HIGH) {
      state = (state + 1) % 3;
    }
    delay(50);
  }
  lastButtonState = buttonState;
}
