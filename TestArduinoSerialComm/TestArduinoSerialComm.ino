long error;
long input;
long output;
double setpoint;


double kp, ki, kd, G, tau;

char mode;   // for incoming serial data

void setup()
{
  Serial.begin(9600);          //  setup serial
 randomSeed(analogRead(0));

  setpoint = 700;

  ////////PID parameters
  tau = 1000.;// in s and obtained from the time constant as we apply a step function
  G = 1.; //gain that we want to use. We find it by adjusting it to be small enough such that the system is not oscillating
  kp = G;
  ki = G / tau;
  kd = 0;
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
  Serial.println(tau, DEC);
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
      ki = G / tau;
      }
    if (mode == 'i') {
      tau = Serial.parseFloat(); 
      kp = G;
      ki = G / tau;
      }
  }

}
