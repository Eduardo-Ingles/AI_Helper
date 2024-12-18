import {Component} from '@angular/core';
import {MatButtonModule} from '@angular/material/button';
import {MatSidenavModule} from '@angular/material/sidenav';
import { ElementRef, ViewChild } from '@angular/core';


import {MatCardModule} from '@angular/material/card';
import { SliderFormattingExample } from "../customSlider-example/slider-formatting-example";
import {MatGridListModule} from '@angular/material/grid-list';


/**
 * @title Autosize sidenav
 */
@Component({
    selector: 'sidenav-autosize-example',
    templateUrl: 'sidenav-autosize-example.html',
    styleUrl: 'sidenav-autosize-example.css',
    standalone: true,
    imports: [ 
        MatSidenavModule, 
        MatButtonModule, 
        SliderFormattingExample,
        MatGridListModule,
        MatCardModule
    ],
})
export class SidenavAutosizeExample {
    
    description_Temperatura = `Controlla la casualità e la creatività delle risposte generate.
    (0 = risultati deterministici / 1 = risultati creativi)`;
    description_Top_P = `Lower top-p values reduce diversity and focus on more probable tokens`;
    description_Top_K = `Lower top-k also concentrates sampling on the highest probability tokens for each step.`;
    description_RepeatPenality = 'discourage the model from generating repetitive text or phrases.';

    showSideBar = false;
    showTemperatura = false;
    showTop_K = false;
    showTop_P = false;
    showRepeatPenalty = false;

    flagsDict = {
        "mainFlag": this.showSideBar,
        "temperatura_Flag": this.showTemperatura,
        "top_K_Flag": this.showTop_K,
        "top_P_Flag": this.showTop_P,
        "repeatPenalityFlag": this.showRepeatPenalty
    };

    //mainFlag = this.showFiller;
    //temperatura_Flag = this.showTemperatura;
    //top_K_Flag = this.showTop_K;
    //top_P_Flag = this.showTop_P;

    
    resizeNavArea(event: Event): void {
		//const textarea = event.target as HTMLTextAreaElement;
        this.flagsDict.mainFlag = !this.flagsDict.mainFlag;
		navBarResize(this.flagsDict);
    }

    salvaParamteriLLM(event: Event): void {
        console.log(this.flagsDict)
    }
}


function navBarResize(flagsDict:any): void {
    
    var exampleStyle = (<HTMLInputElement>document.getElementById("example-container")).style
    //console.log(showFiller, "Resize!", exampleStyle.height)
    if(flagsDict.mainFlag){
        exampleStyle.height = "99%";
        exampleStyle.width = "99%";
    }else{
        exampleStyle.height = "auto";
        exampleStyle.width = "auto";
    }
}