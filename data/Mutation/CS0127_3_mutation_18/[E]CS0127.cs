﻿using System.Collections;
using System.Collections.Generic;
public class MethodeReturn {
  static void LongHypo(float a, float b) {
    /* inserted */
    int _20 = 3;
    float SommeCar = a * a + b * b;
    return SommeCar;
  }
  void Start() {
    float result = LongHypo(3, 4);
    result++;
  }
  void Update() {}
  static void Main() {}
}
