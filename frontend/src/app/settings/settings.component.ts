import { Component } from '@angular/core';
import { HttpClient , HttpClientModule} from '@angular/common/http';

import {FileTreeComponent} from '../componenti/treeFileViewer/treeFileViewer.component'
import { environment } from '../../enviroments/environment';

interface FileNode {
    name: string;
    type: 'file' | 'directory';
    children?: FileNode[];
    path?: string; // Full path for files
}

@Component({
	selector: 'app-settings',
	standalone: true,
	imports: [FileTreeComponent, HttpClientModule],
	templateUrl: './settings.component.html',
	styleUrl: './settings.component.css'
})
export class SettingsComponent {	
		constructor(private apiService: HttpClient) {}
		
		ngOnInit(): void {
			setTimeout(() => this.getFiles_downloads("tutorials"), 1000);
			setTimeout(() => this.getFiles_downloads("settings"), 1000);
			setTimeout(() => this.getFiles_downloads("root"), 1000);
		}
	
		tutorialsTree:any = []
		settingsTree: any = []
		rootTree: any = []
		getFiles_downloads(target:string) {
			const endpoint = "file-tree/"+target;
			this.apiService.get(environment.api+"/"+endpoint).subscribe({			
				next: (res) => {
					if(target == "tutorials"){
						this.tutorialsTree = res;
					}
					if(target == "settings"){
						this.settingsTree = res;
					}
					if(target == "root"){
						this.rootTree = res;
					}
					//console.log(this.tutorialsTree);
				},
				error: (err) => {
				console.error('Error:', err);
				}
			});
			setTimeout(() => this.getFiles_downloads(target), 120000);
		}
	
		downloadFile(node: FileNode) {
			// Assuming the backend has a download endpoint
			const downloadEndpoint = `download/${node.path}`;
			this.apiService.get(`${environment.api}/${downloadEndpoint}`, {
				responseType: 'blob'
			}).subscribe({
				next: (response) => {
					// Create a blob from the response
					const blob = new Blob([response], { type: 'application/octet-stream' });   
					console.log("Response: ", response);
					// Create a link element and trigger download
					const link = document.createElement('a');
					link.href = URL.createObjectURL(blob);
					link.href = window.URL.createObjectURL(blob);
					link.download = node.name;
					link.click();
				},
				error: (err) => {
					console.error('Download failed', err);
				}
			});
		}

}
