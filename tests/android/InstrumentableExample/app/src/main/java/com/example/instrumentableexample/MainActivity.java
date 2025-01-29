package com.example.instrumentableexample;

import androidx.appcompat.app.AppCompatActivity;

import android.os.Bundle;

public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {

        // Examples for how field accesses
        Parent a = new Parent();
        a.str = taint();
        a.b.str = taint();
        a.b.c.str = taint();
        a.b.c.d.str = taint();

        // Function that will be harnessed
        Parent b = new Parent();
        Parent c = blackBox(b);

        // sink(b);

        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
    }

    public static String taint() {
        return "tainted";
    }

    public static Parent blackBox(Parent p) {
        if (Math.random() < 0.5) {
            return new Parent();
        }
        else {
            p.b = null;
            return null;
        }
    }
}
