﻿namespace ConsoleApplication1 {
  class Program {
    delegate int Del1();
    delegate object Del2();
    static void Main(string[] args) {
      ExampleClass ec = new ExampleClass();
      int i = ec.Method1;
    }
  }
  public class ExampleClass {
    public int Method1() {
      /* inserted */
      int _29 = 5;
      return 1;
    }
    public static ExampleClass Method2() {
      return null;
    }
  }
}
