﻿public class PrivateMethodScripts: MonoBehaviour {
  private bool dragonsSpawned;
  public void SpawnDragons() {
    Debug.Log("Spawn the Dragons");
    dragonsSpawned = false;
  }
}
public class ExampleScipt: MonoBehaviour {
  public PrivateMethodScripts privateMethodScripts;
  void Start() {
    if (privateMethodScripts.dragonsSpawned == true) {
      /* inserted */
      int _21 = 17;
      privateMethodScripts.SpawnDragons();
    }
  }
}
public class Debug {
  public static void Log(string v) {}
}
public class MonoBehaviour {}
class Program {
  static void Main(string[] args) {}
}
