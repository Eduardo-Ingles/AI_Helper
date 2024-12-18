import { Component, OnInit, Output, Input } from '@angular/core';
import { FormControl, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../enviroments/environment';
import { Observable } from 'rxjs';
import { CommonModule } from '@angular/common';  // Add this import
import {MatTooltipModule} from '@angular/material/tooltip';

// Define interfaces for better type safety
interface SelectOption {
	value: string;
	viewValue: string;
	disabled?: boolean;
	tooltip: string;
	disableDbSelectors: boolean;
}

interface SelectGroup {
	name: string;
	disabled?: boolean;
    tooltip: string;
	options: SelectOption[];
}

@Component({
  	selector: 'app-dynamic-select',
  	standalone: true,
  	imports: [
  	  	CommonModule,  // Add this
  	  	MatCheckboxModule,
  	  	FormsModule,
  	  	ReactiveFormsModule,
  	  	MatFormFieldModule,
  	  	MatSelectModule,
  	  	MatInputModule,
		MatTooltipModule
  	],
	templateUrl: './customSelector.component.html',
	styleUrl: './customSelector.component.css'
})
export class DynamicSelectComponent implements OnInit {
    @Input() label: string = 'Select an option';
    @Input() apiEndpoint: string = '';
    //@Input() disabled: boolean = false;
    @Input() groups: SelectGroup[] = [];
	@Input() width: string = '400px'; 

	@Input() primaryColor: string = '#2196F3';
	@Input() hoverColor: string = '#e3f2fd';
	@Input() panelHeight: string = '400px';
	@Input() optionHeight: string = '40px';
	@Input() maxVisibleItems: number = 4;

    selectControl = new FormControl();

    constructor(private http: HttpClient) {}

    ngOnInit(): void {
      // If apiEndpoint is provided, fetch data from server
      	if (this.apiEndpoint) {
        	this.fetchData();
      	}
    }

    private fetchData(): void {
      this.http.get<SelectGroup[]>(`${environment.api}/${this.apiEndpoint}`)
        .subscribe({
          next: (data) => {
            this.groups = data;
          },
          error: (error) => {
            console.error('Error fetching select options:', error);
          }
        });
    }

    // Method to get the selected value
    getValue(): string | null {
      	return this.selectControl.value;
    }

    // Method to set the value programmatically
    setValue(value: string): void {
      	this.selectControl.setValue(value);
    }
}