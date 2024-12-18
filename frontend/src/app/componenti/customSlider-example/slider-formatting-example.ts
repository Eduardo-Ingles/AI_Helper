import {Component, OnInit, inject } from '@angular/core';
import {MatSliderModule} from '@angular/material/slider';

import {JsonPipe} from '@angular/common';
import {FormBuilder, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {MatCheckboxModule} from '@angular/material/checkbox';

/**
 * @title Slider with custom thumb label formatting.
 */
@Component({
    selector: 'slider-formatting-example',
    templateUrl: 'slider-formatting-example.html',
    styleUrl: 'slider-formatting-example.css',
    standalone: true,
    imports: [
        MatSliderModule, 
        MatCheckboxModule,
        JsonPipe,
        ReactiveFormsModule,
        FormsModule

    ],
})
export class SliderFormattingExample implements OnInit{
    minValue: number = 0;
    maxValue: number = 1;
    stepValue: number = 0.1;
    currentValue: number = 0;  // Initial value

	fineTemp: string = ""
	fine_P: string = ""
	fine_K: string = ""


    private readonly _formBuilder = inject(FormBuilder);
    readonly fineTunners = this._formBuilder.group({
        fineTemp: false,
        fine_P: false,
        fine_K: false,
    });
        

    ngOnInit() {
        // You can set initial values here or update them based on your needs
        this.setSliderConfiguration(this.minValue, this.maxValue, this.stepValue);        
    }

    // Method to programmatically update slider configuration
    setSliderConfiguration(min: number, max: number, step: number) {
        this.minValue = min;
        this.maxValue = max;
        this.stepValue = step;
        // Ensure current value is within new bounds
        this.currentValue = Math.max(min, Math.min(max, this.currentValue));
    }

    formatLabel(value: number): string {
        const minVal = this.minValue;
        const maxVal = this.maxValue;
        const step = this.stepValue;        
        if (value >= maxVal/step) {
            return Math.round(value / maxVal/step) + '';
        }
        return `${value}`;
    }
}


function onValueChange(value:number){
    console.log('Slider value changed:', value);
}