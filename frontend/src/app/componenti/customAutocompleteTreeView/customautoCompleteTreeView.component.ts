import {Component, OnInit, Input, inject, Output, EventEmitter} from '@angular/core';
import {FormBuilder, FormsModule, ReactiveFormsModule, FormControl} from '@angular/forms';
import {Observable} from 'rxjs';
import {map, startWith} from 'rxjs/operators';
import {MatSlideToggleModule} from '@angular/material/slide-toggle';
import {AsyncPipe} from '@angular/common';
import {MatAutocompleteModule} from '@angular/material/autocomplete';
import {MatInputModule} from '@angular/material/input';
import {MatFormFieldModule} from '@angular/material/form-field';
import { HttpClient , HttpClientModule} from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { environment } from '../../../enviroments/environment';

import { SharedDataService, SharedDataServiceDict } from './../../shared-data.service';


export interface StateGroup {
	name: string;
	includedScripts: string[];
  }
  
export const _filter = (opt: string[], value: string): string[] => {
	const filterValue = value.toLowerCase();
	return opt.filter(item => item.toLowerCase().includes(filterValue));
};

interface ScriptRequirements{
	database: boolean;		// database qualiy (false) |  prod (true)
	collection: boolean;		// smartScada (false) |  scada (true)
	subCollection: boolean;	// devices (false) |  profiles (true) ! se scada = true
	text: boolean;	// necessita inpu (es. nome galleria)
	file: boolean;	// necessita file upload

}

interface SelectedScript {
	name: string;
	viewName: string;
	disabled?: boolean;
	tooltip: string;
	disableDbSelectors: boolean;
	requirements:ScriptRequirements;
	options: {};
}

interface ScriptListGroups {
	name: string;
	disabled?: boolean;
	scripts: SelectedScript[];
	includedScripts: string[];
}

@Component({
	selector: 'custom-autocomplete-treeview',
	templateUrl: './customautoCompleteTreeView.component.html',
	styleUrl: './customautoCompleteTreeView.component.css',
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
export class CustomAutocomplete implements OnInit{	
	selectedScript:string = "";
	constructor(
		private apiService: HttpClient, 
		private sharedDataService: SharedDataService,
		private sharedDataServiceDict: SharedDataServiceDict
	){}

	@Input() itemsList:ScriptListGroups[] = [];//: viewItemStructure[] = [];
	@Output() selectedScriptEvent = new EventEmitter<string>();

	private _formBuilder = inject(FormBuilder);

	stateForm = this._formBuilder.group({
		stateGroup: '',
	});

	stateGroupOptions?: Observable<StateGroup[]>;

	ngOnInit() {
		
		//this.sharedDataService.updateSharedValue("");

		this.stateGroupOptions = this.stateForm.get('stateGroup')!.valueChanges.pipe(
		startWith(''),
		map(value => this._filterGroup(value || '')),
		);
	}

	private _filterGroup(value: string): StateGroup[] {
		if (value) {
		return this.itemsList
			.map(group => ({name: group.name, includedScripts: _filter(group.includedScripts, value)}))
			.filter(group => group.includedScripts.length > 0);
		}
		return this.itemsList;
	}



	updateSuggestions() {
		// Generate filtered suggestions based on searchText
		const allItems = this.itemsList.flatMap(group => group.includedScripts);
		this.filteredSuggestions = allItems
		  .filter(item => item.toLowerCase().includes(this.searchText.toLowerCase()))
		  .slice(0, 15); // Limit suggestions to top x matches
	  }

	showSuggestions() {
		this.showSuggestionBox = true;
		this.updateSuggestions();
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
		this.selectedScriptEvent.emit(suggestion);
		this.selectedScript = suggestion;
		//this.sharedDataService.updateSharedValue(this.selectedScript);
		this.sharedDataServiceDict.updateSharedValue({selectedScript: suggestion});
		//console.log("selected:", suggestion)
	}

	searchText: string = ''; // Search text for partial matches
	stateFilter: string = ''; // Filter to show items from specific field
	filteredSuggestions: string[] = []; // Suggestions to display in the dropdown
	showSuggestionBox: boolean = true; // Controls visibility of the suggestion box
	showCategoryBox: boolean = false; 

	get filteredGallerie() {
		return this.itemsList
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
		  .filter(group => group.includedScripts.length > 0); // Remove groups with no matching items
	  }

}

