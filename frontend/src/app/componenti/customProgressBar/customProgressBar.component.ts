import { Component, Input } from "@angular/core";
import { ProgressBarMode, MatProgressBarModule } from "@angular/material/progress-bar";
import { FormsModule } from "@angular/forms";

import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';



@Component({
    selector: "custom-progress-bar",
    templateUrl: "customProgressBar.component.html",
    styleUrl: "customProgressBar.component.css",
    standalone: true,
    imports:[
        CommonModule,
        MatCardModule, 
        MatProgressBarModule,
        FormsModule
    ]
})
export class CustomProgressBar{  
    mode: ProgressBarMode = 'determinate';
	@Input() value: number = 0;
    @Input() hidden:boolean = true;
    @Input() clientId: string | null = null;

}

