long error;
long input;
long output;
double setpoint;

double kp, ki, kd, G, tauI, tauD;

char mode;   // for incoming serial data

void setup()
{
  Serial.begin(9600);          //  setup serial
 randomSeed(analogRead(0));

  setpoint = 700;

  ////////PID parameters
  tauI = 1000.;// in s and obtained from the time constant as we apply a step function
  G = 1.; //gain that we want to use. We find it by adjusting it to be small enough such that the system is not oscillating
  kp = G;
  ki = G / tauI;
  kd = G * tauD;
}

void loop() {
  /////////// first part of the wavepacket control
  input = random(1000);
  error = setpoint - input;

  output = random(300);
  Serial.print(setpoint);
  Serial.print(", ");
  Serial.print(input);
  Serial.print(", ");
  Serial.print(error);
  Serial.print(", ");
  Serial.print(output);
  Serial.print(", ");
  Serial.print(G);
  Serial.print(", ");
  Serial.print(tauI);
  Serial.print(", ");
  Serial.println(tauD, DEC);
  delay(1000);

  // send data only when you receive data:
  if (Serial.available() > 0) {
    // read the incoming byte:
    // say what you got:
    mode = Serial.read();
    if (mode == 's') {
      long out;
      setpoint = Serial.parseInt();
    }
    if (mode == 'p') {
      G = Serial.parseFloat();
      kp = G;
      ki = G / tauI;
      kd = G * tauD;
      }
    if (mode == 'i') {
      tauI = Serial.parseFloat();
      ki = G / tauI;
      }
    if (mode == 'd') {
        tauD = Serial.parseFloat();
        kd = G*tauD;
        }
  }
}
