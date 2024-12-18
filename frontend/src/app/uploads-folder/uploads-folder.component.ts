import { Component } from '@angular/core';
import { HttpClient , HttpClientModule} from '@angular/common/http';

//import { AppComponent } from '../app.component';
import {FileTreeComponent} from '../componenti/treeFileViewer/treeFileViewer.component'
import { environment } from '../../enviroments/environment';
//import { AppModule } from '../../app/app.module';

interface FileNode {
    name: string;
    type: 'file' | 'directory';
    children?: FileNode[];
    path?: string; // Full path for files
}

@Component({
	selector: 'app-uploads-folder',
	standalone: true,
	imports: [FileTreeComponent, HttpClientModule],
	templateUrl: './uploads-folder.component.html',
	styleUrl: './uploads-folder.component.css'
})
export class UploadsFolderComponent {
	constructor(private apiService: HttpClient) {}

	//folderTree = TREE_DATA

	ngOnInit(): void {
		setTimeout(() => this.getFiles_uploads(), 100);
	}

	folderTree:any = []
	getFiles_uploads() {
		const endpoint = "file-tree/uploads";
		this.apiService.get(environment.api+"/"+endpoint).subscribe({			
			next: (res) => {
				this.folderTree = res;
				//console.log(this.folderTree);
			},
			error: (err) => {
			console.error('Error:', err);
			}
		});
		
		setTimeout(() => this.getFiles_uploads(), 60000);
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
