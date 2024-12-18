import {Component, Input, inject} from '@angular/core';
import {FormControl, FormsModule, ReactiveFormsModule, FormBuilder} from '@angular/forms';
import {Observable} from 'rxjs';
import {map, startWith} from 'rxjs/operators';
import {MatSlideToggleModule} from '@angular/material/slide-toggle';
import {AsyncPipe} from '@angular/common';
import {MatAutocompleteModule} from '@angular/material/autocomplete';
import {MatInputModule} from '@angular/material/input';
import {MatFormFieldModule} from '@angular/material/form-field';
import { HttpClient , HttpClientModule} from '@angular/common/http';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { environment } from '../../../enviroments/environment';


/*
export interface State {
  flag: string;
  name: string;
  population: string;

}*/
export interface Gallerie {
	name: string;
	includedScripts: string[];
	
  }
  

/**
 * @title Autocomplete overview
 */
@Component({
	selector: 'autocomplete-overview-example',
	templateUrl: './customAutoCompleteInput.component.html',
	styleUrl: './customAutoCompleteInput.component.css',
	standalone: true,
	imports: [
		FormsModule,
		MatFormFieldModule,
		MatInputModule,
		MatAutocompleteModule,
		ReactiveFormsModule,
		MatSlideToggleModule,
		AsyncPipe,
		HttpClientModule,
		CommonModule,
		
	],
})
export class AutocompleteOverviewExample {	
	stateCtrl = new FormControl('');
	
	
	constructor(private apiService: HttpClient) {}
	
	ngOnInit(): void {
		this.getListaGalleria();	
	}

	
	@Input() stepState: boolean = false;

	@Input() gallerie: Gallerie[] = []
	getListaGalleria() {
		const endpoint = "getGallerieList";
		this.apiService.get(environment.api+"/"+endpoint).subscribe({			
			next: (res:any) => {
			this.gallerie = res;
			//this.mainOutputArea = String(JSON.stringify(res));
			//console.log(String(JSON.stringify(res)))
			//console.log(((res[0].gallerie)))
			},
			error: (err) => {
			console.error('Error:', err);
			}
		});
	}


	updateSuggestions() {
		// Generate filtered suggestions based on searchText
		const allItems = this.gallerie.flatMap(group => group.includedScripts);
		this.filteredSuggestions = allItems
		  .filter(item => item.toLowerCase().includes(this.searchText.toLowerCase()))
		  .slice(0, 15); // Limit suggestions to top x matches
	  }

	showSuggestions() {
		this.showSuggestionBox = true;
		this.updateSuggestions();
		//console.log(this.stateFilter)
	}

	hideSuggestions() {
		// Delay hiding to allow click event on suggestion to complete
		setTimeout(() => {
		  this.showSuggestionBox = false;
		}, 200);
	}

	applySuggestion(suggestion: string) {
		this.searchText = suggestion;
		this.updateSuggestions();
		this.hideSuggestions();
	}

	searchText: string = ''; // Search text for partial matches
	stateFilter: string = ''; // Filter to show items from specific field
	filteredSuggestions: string[] = []; // Suggestions to display in the dropdown
	showSuggestionBox: boolean = true; // Controls visibility of the suggestion box
	showCategoryBox: boolean = false; 

	get filteredGallerie() {
		return this.gallerie
		  .filter(group =>
			// Filter by state name if stateFilter is set
			(!this.stateFilter || group.name.toLowerCase().includes(this.stateFilter.toLowerCase()))
		  )
		  .map(group => ({
			...group,
			// Filter gallerie items based on searchText
			gallerie: group.includedScripts.filter(item =>
			  !this.searchText || item.toLowerCase().includes(this.searchText.toLowerCase())
			)
		  }))
		  .filter(group => group.gallerie.length > 0); // Remove groups with no matching items
	  }
}