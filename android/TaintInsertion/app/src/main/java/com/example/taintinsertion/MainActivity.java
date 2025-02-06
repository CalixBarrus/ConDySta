package com.example.taintinsertion;

import androidx.appcompat.app.AppCompatActivity;

import android.os.Bundle;

public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {

        String secret = TaintInsertion.taint();

        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
    }
}

