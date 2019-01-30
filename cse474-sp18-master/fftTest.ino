unsigned int EKGSampleFreq; // = 10000
int N = 256;

typedef struct _ComplexData {
  int real;
  int imag;
} Complex;

Complex EKGRawBuf[256];

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
}

int once = 0;

void loop() {
  // put your main code here, to run repeatedly:
  //if (once == 0) {
      capture();
      FFT();
      getFrequency();
  //}
  //once = 1;
}

void capture() {
  int start = micros();
  for (int i = 0; i < N; i++){
    EKGRawBuf[i].real = analogRead(A0);
    //EKGRawBuf[i].imag = 0;
    //Serial.print("Index: ");
    //Serial.print(i);
    //Serial.print("; Real: ");
    //Serial.println(EKGRawBuf[i].real);
    //Serial.print("; Imag: ");
    //Serial.println(EKGRawBuf[i].imag);
    //delay(100);
  }
  int finish = micros();
  EKGSampleFreq = 1000000*N/(finish - start);
  for(int i = 0; i < N; i++){
    EKGRawBuf[i].imag = 0;
  }
  //Serial.print("Capture complete, sample frequency = ");
  //Serial.println(EKGSampleFreq);
  //process();
}

void process(){
  FFT();//(EKGRawBuf, 256);
}

void FFT(){
  Complex temp[N];
  //memcpy(temp, x, 256*sizeof(int));
  //std::copy(std::begin(x), std::end(x), std::begin(temp));

  for(int i = 0; i < N; i++){
    temp[i] = EKGRawBuf[i];
  }

  Serial.println("---------------------");
  
  //Complex sum;
  for (int k = 0; k < N; k++) {
    for (int n = 0; n < N; n++) {
      float pi = 3.14159;
      float theta = n * k * 2 * pi / N;
      int r = temp[n].real;
      EKGRawBuf[k].real += r*cos(theta);
      EKGRawBuf[k].imag += r*sin(theta);
      //Serial.print("Index: ");
      //Serial.print(i);
      //Serial.print("; theta: ");
      //Serial.print(theta);
      //Serial.print("; EKGRawBuf[i]: ");
      //Serial.print(EKGRawBuf[i].real);
      //Serial.print("; temp[i].real: ");
      //Serial.println(r);
    }
      //Serial.println("---------");
      //Serial.print("Index: ");
      //Serial.print(k);
      //Serial.print("; Real: ");
      //Serial.print(x[k].real);
      //Serial.print("; Imag: ");
      //Serial.println(x[k].imag);
  }
  Serial.println("FFT complete");
  //getFrequency(x, N, EKGSampleFreq);
}

void getFrequency(){//Complex x[], int N, int fs){
  Serial.println("--------------");
  //float signalFreq;
  int maxVal = 0;
  int max_index = 0;
  int halfRange = N/2;
  // find index of max magnitude in x
  for (int i = 0; i < halfRange; i++) { // half-range
    float magnitude = sqrt(pow(EKGRawBuf[i].real,2) + pow(EKGRawBuf[i].imag,2));
    //Serial.print("Index: ");
    //Serial.print(i);
    //Serial.print("; Magnitude: ");
    //Serial.print(magnitude);
    if (magnitude > maxVal) {
      max_index = i;
      maxVal = magnitude;
    }
    //Serial.print("; Max Val: ");
    //Serial.print(maxVal);
    //Serial.print("; Max index: ");
    //Serial.println(max_index);
  }
  Serial.print("Sample frequency: ");
  Serial.print(EKGSampleFreq);
  Serial.print("; Max index: ");
  Serial.print(max_index);
  Serial.print("; N: ");
  Serial.print(N);
  Serial.print("; Signal frequency: ");
  int signalFreq = (EKGSampleFreq * max_index) / N; //(float)(EKGSampleFreq*max_index)/(float)N;
  Serial.println(signalFreq);
  // EKGFreqBuf[EKGFreqBufferIndex] = signalFreq;
}
