package com.example.instrumentableexample;

public class Child {
    public String str;
    public SubChild c; 

    public class SubChild {
        public String str;
        public SubSubChild d;
        public SubChild() {
            d = new SubSubChild();
            str = "";
        }
    }

    public class SubSubChild {
        public String str;
        public SubSubChild() {
            str = "";
        }
    }

    public Child() {
        str = "";
        c = new SubChild();
    }
}
