import {Component, Input} from '@angular/core';
import {ProgressSpinnerMode, MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {MatSliderModule} from '@angular/material/slider';
import {FormsModule} from '@angular/forms';
import {MatRadioModule} from '@angular/material/radio';
import {MatCardModule} from '@angular/material/card';

@Component({
    standalone: true,
    selector: 'custom-progress-spinner',
    templateUrl: 'customprogressspinner.component.html',
    styleUrl: 'customprogressspinner.component.css',
    imports: [MatCardModule, MatRadioModule, FormsModule, MatSliderModule, MatProgressSpinnerModule],
})
export class CustomProgressSpinner {
    //mode: ProgressSpinnerMode = 'determinate';
    @Input() mode: ProgressSpinnerMode = "indeterminate";
    @Input() value = 0;
    @Input() hideSpinner: any;
    @Input() color: any;
}
