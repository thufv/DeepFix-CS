﻿using System;
class Program {
  static void Main() {
    /* inserted */
    int _18 = 19;
    try {} catch(Exception ex) {
      string MyException = ex.ToString;
      Console.WriteLine(MyException);
    }
  }
}