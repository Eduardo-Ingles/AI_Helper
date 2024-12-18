import { Component } from '@angular/core';
import { RouterModule, RouterOutlet, RouterLink, Routes } from '@angular/router';
import {CustomNavBarComponent} from './custom-nav-bar/custom-nav-bar.component'

import {FileTreeComponent} from './componenti/treeFileViewer/treeFileViewer.component'

import { SharedDataService } from './shared-data.service';
import { HomeComponent } from './home/home.component';

import {FileUploaderComponent} from "./componenti/file-uploader/file-uploader.component";

import {DownloadsFolderComponent} from "./downloads-folder/downloads-folder.component";

import {TableDynamicArrayDataExample} from "./componenti/dynamicTable/dynamicTable.component";


@Component({
	selector: 'app-root',
	standalone: true,
	imports: [RouterModule, RouterOutlet, RouterLink, CustomNavBarComponent, FileTreeComponent, HomeComponent, FileUploaderComponent],
	templateUrl: './app.component.html',
	styleUrl: './app.component.css'
	})
export class AppComponent {
	title = 'Automazione';


	
  	//currentValue: string; --> 
	/*
	<div>
		<h3>Component 1</h3>
		<p>Shared Value: {{ currentValue }}</p>
		<button (click)="updateValue('New Value from Component 1')">Update Value</button>
	</div>
	*/
	constructor(private sharedDataService: SharedDataService) {
		var currentValue = "";
		// Subscribe to the shared value observable
		this.sharedDataService.sharedValue$.subscribe(value => {
		currentValue = value; // this.
		});
	}

	// Update the shared value
	updateValue(newValue: string): void {
		this.sharedDataService.updateSharedValue(newValue);
	}
	
}
