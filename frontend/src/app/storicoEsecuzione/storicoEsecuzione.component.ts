import { Component, OnInit, Output, Input, inject, signal, ChangeDetectionStrategy } from '@angular/core';
import { HttpClient , HttpClientModule} from '@angular/common/http';
import { environment } from '../../enviroments/environment';

import {MatExpansionModule} from '@angular/material/expansion';
//import { AppComponent } from '../app.component';
import {FileTreeComponent} from '../componenti/treeFileViewer/treeFileViewer.component'
//import { AppModule } from '../../app/app.module';
import { TableDynamicArrayDataExample } from '../componenti/dynamicTable/dynamicTable.component';
import {MatBadgeModule} from '@angular/material/badge';


export interface PeriodicElement {
    owner: string;
    task: string;
    position: number;
    messages: string [];
    status: string;
}


@Component({
	selector: 'app-uploads-folder',
	standalone: true,
	imports: [
        FileTreeComponent, 
        HttpClientModule, 
        MatExpansionModule,
        TableDynamicArrayDataExample,
		MatBadgeModule
    ],
	templateUrl: './storicoEsecuzione.component.html',
	styleUrl: './storicoEsecuzione.component.css'
})
export class StoricoEsecuzioneComponent implements OnInit{
    constructor(private apiService: HttpClient){}
	readonly panelOpenState = signal(false);


	ngOnInit(): void {	
		this.initFunctions();	
	}
	
	ngOnDestroy(): void {}

	
	async initFunctions() {
		await this.getScriptList(); 
	}
	
	itemsCount: number = 0;
	scriptsList: any = [];
	async getScriptList(): Promise<void> {
		const endpoint = "getScriptList";
		return new Promise((resolve, reject) => {
			this.apiService.get(environment.api + "/" + endpoint).subscribe({ 
				next: (res) => {
					this.scriptsList = res; // Parse directly without `JSON.stringify`
					//console.log(this.scriptsList)
					resolve(); // Resolve the promise when the request completes
				},
				error: (err) => {
					console.error('Error:', err);
					reject(err); // Reject the promise on error
				},
			});
		});
	}
	
}