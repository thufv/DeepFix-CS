﻿public class Program {
  static void Main(string[] args) {
    /* inserted */
    int _13 = 21;
  }
  public string ReturnItemName(int index) {
    for (int i = 0; i < ItemList.Length; i++) {
      if (ItemList[i].Id == index) {
        return ItemList[i].Name;
      }
    }
    string defaultValue = "";
  }
  public Item[] ItemList;
}
public struct Item {
  public int Id;
  public string Name;
}
