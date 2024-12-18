import {Component, OnInit, ViewChild, inject, ChangeDetectionStrategy, Input} from '@angular/core';
import {MatTable, MatTableModule} from '@angular/material/table';
import {MatButtonModule} from '@angular/material/button';
import { environment } from '../../../enviroments/environment';
import { HttpClient , HttpClientModule} from '@angular/common/http';
import {
    MAT_DIALOG_DATA,
    MatDialog,
    MatDialogActions,
    MatDialogClose,
    MatDialogContent,
    MatDialogTitle,
} from '@angular/material/dialog'

import {ProgressSpinnerMode, MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import { CustomProgressSpinner } from '../customProgressSpinner/customprogressspinner.component';

export interface PeriodicElement {
    position: number;
    owner: string;
    timestamp: string;
    task: string;
    files: string;
    text: string;
    db: string;
    messages: string [];
    status: number;
}

@Component({
	standalone: true,
    selector: 'table-dynamic-array-data-example',
    styleUrl: 'dynamicTable.component.css',
    templateUrl: 'dynamicTable.component.html',
    imports: [
        MatButtonModule, 
        MatTableModule,
        CustomProgressSpinner
    ],    
})
export class TableDynamicArrayDataExample implements OnInit{

	constructor(private apiService: HttpClient) {}

    dataHolder: PeriodicElement[] = [];
    displayedColumns: string[] = ['position', 'timestamp', 'owner', 'task', 'files', 'text', 'messages', 'status'];
    //dataSource = [...ELEMENT_DATA];
    dataSource = [...this.dataHolder];
    
    spinnerMode: ProgressSpinnerMode = "determinate";

    @ViewChild(MatTable) table!: MatTable<PeriodicElement>;
	
    @Input() taskname: any;

    reload = true;
	ngOnInit(): void {	
        this.loadTasks();			
	}
	
	ngOnDestroy(): void {
        this.reload = false;
    }

    //readonly dialog = inject(MatDialog);
    dialog = inject(MatDialog);
    openDialog(msg: string) {
        this.dialog.open(DialogElementsExampleDialog, {data: msg, 
            maxWidth: '80vw',
            maxHeight: '90vh',
            height: '100%',
            width: '100%',
            panelClass: 'full-screen-modal'
        });
        //console.log(msg)
    }

    addData() {
        this.dataSource.push(this.dataHolder[this.dataSource.length]);
        this.table.renderRows();
    }

    removeData() {
        this.dataSource.pop();
        if(this.dataSource){
            this.table.renderRows();
        }
    }

    msgs = [];
    hideSpinner = false;
    loadTasks(){
		const endpoint = "getalltasks";
		this.apiService.get(environment.api+"/"+endpoint).subscribe({			
			next: (res:any) => {
			    //console.log(">", res)		
                this.msgs = res;
			    //console.log(">", this.msgs)	
                Object.keys(res).forEach((element: any) => {
                    let colore = "primary"
                    //console.log(">", element)	
                    if(this.taskname && res[element].task === this.taskname || this.taskname === "Miscelanea"){
                        //console.log("res[element].task: ", res[element].task)                    
                        if(res[element].progress > 0 && res[element].progress < 99.9){
                            colore = "warn";
                            this.hideSpinner = false;
                        }else{
                            colore = "primary"
                            //this.hideSpinner = true;
                        }                        
                        let tempMsg = "";
                        //console.log(res[element])
                        res[element].message.forEach((element: any) => {                            
                            if("message" in element){
                                tempMsg += element.message + "\n";
                            }
                            if("stream" in element){
                                tempMsg += element.stream;
                            }
                        });

                        
                        if(res[element].links){
                            //console.log("link: ",res[element].links)
                            tempMsg += "\n";
                            res[element].links.forEach((link: any) => {                                    
                                //tempMsg += link.linkName;                                  
                                tempMsg += link.linkName;
                            });
                        }
                        
                        var newElement: any = 
                        {
                            position: this.dataHolder.length,
                            owner: res[element].clientName,
                            task: res[element].task,
                            timestamp: res[element].timestamp,
                            text: res[element].data.galleria,//.data[galleria],
                            files: res[element].data.files,//.datafiles
                            db: res[element].data.database,//[database],
                            //messages: res[element].message.toString(),
                            messages: tempMsg,
                            status: res[element].progress,
                            colore: colore
                        };
                        //console.log("newElement", newElement)
                        if(!this.dataHolder.includes(newElement.clientName)){
                            this.dataHolder.push(newElement);	
                            this.dataSource = [...this.dataHolder];
                        }	
                    
                        if(this.dataHolder.length != 0 && this.reload === true){
                            this.table.renderRows();
                        }
                    }
                });
			},
			error: (err) => {
			console.error('Error:', err);
			}
		});
        setTimeout(() => this.test(), 500);
	}

    test(){
        if(this.reload === true){
            setTimeout(() => this.loadTasks(), 1000);
            this.dataHolder = []
            if(this.dataHolder.length != 0){
                this.table.renderRows();
            }
        }
    }
}


@Component({
	standalone: true,
    selector: 'dialog-data-example-dialog',
    templateUrl: 'dynamicTable.data.html',
    styleUrl: 'dynamicTable.data.css',
    imports: [MatDialogTitle, MatDialogContent, MatDialogActions, MatDialogClose, MatButtonModule],
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DialogElementsExampleDialog {
    data = inject(MAT_DIALOG_DATA);
}