﻿public class PrivateMethodScripts: MonoBehaviour {
  public bool dragonsSpawned;
  private void SpawnDragons() {
    Debug.Log("_Spawn the Dragons"
    /* updated */
    );
    dragonsSpawned = false;
  }
}
public class ExampleScipt: MonoBehaviour {
  public PrivateMethodScripts privateMethodScripts;
  void Start() {
    if (privateMethodScripts.dragonsSpawned == true) {
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
