import { Component, OnInit, Output, Input, inject, signal, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient , HttpClientModule} from '@angular/common/http';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatBottomSheet, MatBottomSheetModule, MatBottomSheetRef} from '@angular/material/bottom-sheet';
import {MatListModule} from '@angular/material/list';
import {MatButtonModule} from '@angular/material/button';
import {MatTooltipModule} from '@angular/material/tooltip';
import {DynamicSelectComponent} from "../componenti/customSelector/customSelector.component";
import {CustomProgressBar} from "../componenti/customProgressBar/customProgressBar.component";
import { ProgressService } from '../progress.service';
import { environment } from '../../enviroments/environment';

import {MatAutocompleteModule} from '@angular/material/autocomplete';
import {MatFormFieldModule} from '@angular/material/form-field';
import {WebSocketService } from "../api.service";

import {WebSocketClientComponent} from './wsComponent.component'
import {CustomFileDownloader} from '../componenti/customFileDownloader/customFileDownloader.component'

import {Observable} from 'rxjs';
import {startWith, map, timeInterval} from 'rxjs/operators';

import {MultiButtonToggleMode} from '../componenti/customMultiToggler/customMultiToggler.component'

import {CustomDialogBoxDisplay} from "../componenti/customDialogBox-Display/customDialogBoxDisplay.component";
import {CustomDialogBoxInput} from "../componenti/customDialogBox-Input/customDialogBoxInput.component";

import {AutocompleteOverviewExample} from "../componenti/customAutoCompleteInput/customAutoCompleteInput.component";

import {FileUploaderComponent} from "../componenti/file-uploader/file-uploader.component";
import { SharedDataService, SharedDataServiceDict } from '../shared-data.service';

import {MatRadioModule} from '@angular/material/radio';
import {MatButtonToggleModule} from '@angular/material/button-toggle';
import {MatStepperModule} from '@angular/material/stepper';
import {MatIconModule} from '@angular/material/icon';
import {FormBuilder, Validators, FormsModule, ReactiveFormsModule, FormControl, AbstractControl, ValidationErrors, ValidatorFn} from '@angular/forms';

import {CustomAutocomplete} from "../componenti/customAutocompleteTreeView/customautoCompleteTreeView.component";

import {TextFieldModule} from '@angular/cdk/text-field';
import {MatInputModule} from '@angular/material/input';

import {SnackBarOverviewExample} from '../componenti/snackBar/snackBar.component';

import {MatExpansionModule} from '@angular/material/expansion';

import {MatSnackBar} from '@angular/material/snack-bar';

import { SocketService } from '../socket.service';

import { io, Socket } from 'socket.io-client';

import {DomSanitizer, SafeResourceUrl, SafeUrl} from '@angular/platform-browser';


export interface customSearchView {
	name: string;
	items: string[];
}

export interface ScriptsGroup {
	name: string;
	includedScripts: string[];
}

export const _filter = (opt: string[], value: string): string[] => {
	const filterValue = value.toLowerCase();
	return opt.filter(item => item.toLowerCase().includes(filterValue));
};

export interface Gallerie {
	name: string;
	includedScripts: string[];
}

export interface chosenData{
	script: string;
	db_prod: boolean;
	smartScadaCollection: boolean;
	deviceCollection: boolean;
	galleria: string;
	fileList: string[];
}
  
export interface RequiredFields{
	database: boolean;
	collection: boolean;
	subCollection: boolean
	file: boolean;
	text: boolean
}


type LinkObject = { link: string; linkName: string };

@Component({
  	selector: 'app-home',
  	standalone: true,
  	imports: [
			MatIconModule,
			MatButtonToggleModule, 
			HttpClientModule, 
			MatSlideToggleModule, 
			FormsModule, 
			CommonModule,
			DynamicSelectComponent,
			CustomProgressBar,
			WebSocketClientComponent,
			CustomFileDownloader,
			MultiButtonToggleMode,
			CustomDialogBoxDisplay,
			CustomDialogBoxInput,
			AutocompleteOverviewExample,
			FileUploaderComponent,
			MatRadioModule,
			MatStepperModule,
			MatAutocompleteModule,
			
			CustomAutocomplete,
			MatInputModule,
			TextFieldModule,
			ReactiveFormsModule,
			MatButtonModule,
			MatTooltipModule,	
			MatExpansionModule					
		],
	templateUrl: './home.component.html',
	styleUrl: './home.component.css'
})
export class HomeComponent implements OnInit{

	/* Variabili */ 	
	readonly panelOpenState = signal(false);
    private _snackBar = inject(MatSnackBar);
	private _formBuilder = inject(FormBuilder);

	myControl = new FormControl('');
	scriptsFormGroup = this._formBuilder.group({
	  	scriptsCtrl: ['', Validators.required],
	});
	secondFormGroup = this._formBuilder.group({
	  	secondCtrl: '',
		database: ['', Validators.required],
	});
	tirthFormGroup = this._formBuilder.group({
		tirthCtrl: '',
		collection: '',
		subCollection: '',
	});
	forthFormGroup = this._formBuilder.group({
		myControl: this.myControl,
		files: ''
	});

	disableTirthFormGroupFlag:boolean = false;
	tooltipsHolder:any = 
	{
		showDelay: "1250",
		hideDelay: "500",
		btn_next: "Avanti",
		btn_back: "Indietro",
		btn_reset: "Resetta di tutto il form!",
		btn_esegui: "Esegui lo script con i dati selezionati..."
	}


	private globalSocket!: Socket;
	@Output() mainOutputArea: string = "";
	hideMainOutput = true;
	hideSelector = false;
	isOptional = false;
	currentStep = "0"
	dangerousUrl = "";
	tutorialText = "";
	options: string[] = [];
	scriptMessages: string[] = [];
	serverMessage!: string;	
	templateFile: string = "";/* ########### */
	textAreaMessages: string = "";
	listaGallerie: Gallerie[] = []
	scriptsList: any = [];
	filteredOptions!: Observable<string[]>;
	trustedUrl: SafeUrl;

	/* Constructor */	
	constructor(
		private apiService: HttpClient, 
		private progressService: ProgressService, 
		private webSocketService: WebSocketService,
		private sharedDataService: SharedDataService,
		private sharedDataServiceDict: SharedDataServiceDict,
		private sanitizer: DomSanitizer
	){		
		this.sharedDataService.sharedValue$.subscribe(value => {
			this.selectedScript = value;
			if(this.stepOneFlag === true){
				this.valStep1.valore = value;
			}else{				
				this.valStep1.valore = this.valStep1.default;
			}
		});		
		this.socketStart();		
		this.trustedUrl = sanitizer.bypassSecurityTrustUrl(this.dangerousUrl);	
	}

	socketStart(){
		this.globalSocket = io(`http://${environment.ip}:${environment.porta}`, {
			transports: ['websocket', 'polling'],
			forceNew: true,
			path: "/socket.io/",
			query: { client_id: this.clientID },
			reconnection: true,
			withCredentials: false
		});
	}
	

	/* Funzioni */
	ngOnInit(): void {		
		this.initFunctions();	
		this.initializeListaGallerie();		
		this.getScriptTutorial("default");
	}
	
	ngOnDestroy(): void {

		if(this.globalSocket) {
			console.log("Disconnessione socketio");
			this.globalSocket.disconnect();
			//setTimeout(() => this.globalSocket.disconnect(), 3000);
			
		}
		this.isRunning = false;	
	}

	/* ------------------------------------- */


	durationInSeconds = 5;
	openSnackBar(messaggio: string) {
		this._snackBar.open(messaggio, "chiudi", {duration: 5000});
	}


	choicesMade: any = {}
  	submissionData: any = {};
	isRunning: boolean = false;
	cardModeAggiungi: boolean = true;  //aggiunto 04/03/26
	async esegui(){
		var uploadedFiles;
		this.sharedDataServiceDict.sharedValue$.subscribe(value => {			
			uploadedFiles = value["fileNames"];
		  });

		var temp_script = this.scriptsFormGroup.value.scriptsCtrl;
		var temp_db = this.secondFormGroup.value.database;
		var temp_collection = this.tirthFormGroup.value.collection;
		var temp_subCollection = this.tirthFormGroup.value.subCollection;
		var temp_galleria = this.forthFormGroup.value.myControl;

		if(!uploadedFiles){
			uploadedFiles = null;
		}
		this.submissionData = 
			{
				script: temp_script,
				database: temp_db,
				collection: temp_collection,
				subCollection: temp_subCollection,
				galleria: temp_galleria,
				files: uploadedFiles,
				mode: this.cardModeAggiungi ? 'create' : 'update'
			}
		//console.log("choicesMade: ", this.submissionData);
		if((this.selectionRequirements.text && this.submissionData.galleria) || (this.selectionRequirements.file && this.submissionData.files)){	
			console.log("this.globalSocket.id: ", this.globalSocket.id)
			this.submissionData.userId = this.globalSocket.id;//"UUID";
			this.isRunning = true;
			this.hideMainOutput = false;	
			console.log("MODE:", this.submissionData.mode, "| cardModeAggiungi:", this.cardModeAggiungi); // <-- aggiungi
			this.runScript();	
		}else{
			if(this.selectionRequirements.text && !this.submissionData.galleria){
				this.openSnackBar("Errore: Inserire nome galleria");
			}
			if(this.selectionRequirements.file && !this.submissionData.files){
				this.openSnackBar("Errore: nessun file caricato!");
			}
		}
	}
	
	handleSocket(){
		const socket: Socket = io(`${environment.ip}/${environment.porta}`);
		console.log("socket: ", socket)
		if(this.clientID){
			const userId = this.clientID;
			// Listen for the event specific to the user
			socket.on(`script_status_${userId}`, (data: { output: string }) => {
				console.log("Received output:", data.output);
				//this.textAreaMessages += data.output;// Handle the received output here
			});
			// Optional: Handle connection errors
			socket.on("connect_error", (err: Error) => {
				console.error("Connection error:", err.message);
			});
		}

		socket.on("disconnect", () => {
			console.log("Disconnected from server.");
		});
	}
	

	//public sanitizer!: DomSanitizer;
	//safeHTML(unsafe: string) {
	//	return this.sanitizer.bypassSecurityTrustHtml(unsafe);
	//}

	linksFlag: boolean = false;
	testLink : LinkObject[] = [];//{link: "", linkName: ""};
	
	outputDiv:string = "";
	clientID!: any;
	progressBarValue = 0;
	hiddenProgressBar: boolean = true;
	sanitizedLink: any;
	async runScript(){
		//console.log(this.isRunning);
		const endpoint = 'runScript';
		this.apiService.post<any>(`${environment.api}/${endpoint}`, this.submissionData).subscribe({
			next: (res) => {
				this.clientID = res.client_id;
				//console.log('POST Response:', (res.client_id));				
				
				//console.log(this.globalSocket.id);
				this.globalSocket.on(`response:${this.clientID}`, (message: any) => {
            	    //console.log('Targeted Server Response:', message);
            	    //this.textAreaMessages += message.data + "\n";	
					
					if(message.stream){
						this.outputDiv +=  message.stream;				
					}
					
					if(message.data){
						this.outputDiv += message.data + "\n";
						if(this.hiddenProgressBar === false && message.progress && message.progress >= 99.5){
							this.progressBarValue = 100;
						}
					}

					if(message.links){
						console.log("message.link: ", message.links)
						message.links.forEach((link: any) => {
							console.log(link);
							this.linksFlag = true;
							let linky = {link: link.link, linkName: link.linkName}
							this.testLink.push(linky);
							//this.testLink.linkName = ;
						//this.dangerousUrl = message.link;
						//this.sanitizedLink = this.sanitizer.bypassSecurityTrustUrl(message.link);
							//this.outputDiv += '<a href = "#" (click) = ' + this.downloadFile(link.link, link.linkName) + '">' + link.linkName + '</a>'; 
						//this.outputDiv += this.sanitizer.bypassSecurityTrustScript('<a href=sanitizedLink target = "_blank" (click)="downloadFile(testLink.link)"> <mat-icon>file_copy</mat-icon> {{testLink.linkName}}	</a>')//this.sanitizer.bypassSecurityTrustScript('<a href="javascript:void(0)"  (click)="downloadFile(testLink.link)"> <mat-icon>file_copy</mat-icon> {{testLink.linkName}}	</a>')
						});
					}

					//this.sanitizer.bypassSecurityTrustHtml('<button  (click) = "downloadFile(sanitizedLink)"> DNLD </button>')
    				//this.dangerousUrl = 'javascript:alert("Hi there")';
    				//this.trustedUrl = sanitizer.bypassSecurityTrustUrl(this.dangerousUrl);

					if(message.progress){
						this.hiddenProgressBar = false;
						//console.log(message.progress);
						this.progressBarValue = message.progress;
						if(message.progress > 99.5){
							setTimeout(() => this.hiddenProgressBar = true, 3000);
						}
					}
            	});
			},
			error: (err) => {
			console.error('Error in POST:', err);
			this.clientID = 'Failed to send data';
			}
		});
	}

	downloadFile(filePath: string, linkName: string) {
        // Assuming the backend has a download endpoint
		console.log("filePath: ", filePath)
        const downloadEndpoint = `download/${filePath}`;
        this.apiService.get(`${environment.api}/${downloadEndpoint}`, {
            responseType: 'blob'
        }).subscribe({
            next: (response) => {
                // Create a blob from the response
                const blob = new Blob([response], { type: 'application/octet-stream' });   
				//console.log("Response: ", response);
                // Create a link element and trigger download
                const link = document.createElement('a');
				link.href = URL.createObjectURL(blob);
                link.href = window.URL.createObjectURL(blob);
                link.download = linkName;
                link.click();
            },
            error: (err) => {
                console.error('Download failed', err);
            }
        });
    }

	downloadLinkFile(filePath: string, linkName: string) {
        const downloadEndpoint = `download/${filePath}`;
		//console.log("Link download:", filePath, " - ", linkName)
        this.apiService.get(`${environment.api}/${downloadEndpoint}`, {
            responseType: 'blob'
        }).subscribe({
            next: (response) => {
                const blob = new Blob([response], { type: 'application/octet-stream' });   
				console.log("Response: ", response);
                const link = document.createElement('a');
				link.href = URL.createObjectURL(blob);
                link.href = window.URL.createObjectURL(blob);
                link.download = linkName;
                link.click();
            },
            error: (err) => {
                console.error('Download failed', err);
            }
        });
    }


	selectionRequirements_!: RequiredFields;
	selectionRequirements = {
		database: false,
		collection: false,
		subCollection: false,
		file: false,
		text: false,
	};


	checkScriptSettings(currSelectedScript:string){	
		this.scriptsList.forEach((group:any) => {	
			group.scripts.forEach((script: any) => {	
				if(currSelectedScript === script.viewName){
					//console.log(">", currSelectedScript, ": ", group.name, " - " , script.name, "requirements:", script.requirements, "templateFile:", script.templateFile)
					this.templateFile = script.templateFile;
					this.selectionRequirements = script.requirements
					this.getScriptTutorial(currSelectedScript);
				}		
			});
		});
		//console.log("selectionRequirements > ", this.selectionRequirements);
	}

	getScriptTutorial(selectedScript: string){
		let turorialText = "";
		if(!selectedScript || selectedScript === ""){
			selectedScript = "default";
		}
		const endpoint = "getScriptTutorial";
		this.apiService.get(environment.api+"/"+endpoint + "/" + selectedScript).subscribe({			
			next: (res:any) => {
				this.tutorialText = res;	
				//console.log(">", turorialText)			
			},
			error: (err) => {
			console.error('Error:', err);
			}
		});
		
	}

	/* Script Filter */ 	
	async initFunctions() {
		try {
			await this.getScriptList();
			await this.mapScriptsGroups();
		} catch (err) {
			console.error('Failed to initialize scripts:', err);
		}
	}

	getScriptList(): Promise<void> {
		const endpoint = "getScriptList";
		return new Promise((resolve, reject) => {
			this.apiService.get(environment.api + "/" + endpoint).subscribe({ 
				next: (res) => {
					this.scriptsList = res; // Parse directly without `JSON.stringify`
					//console.log(res)
					resolve(); // Resolve the promise when the request completes
				},
				error: (err) => {
					console.error('Error:', err);
					reject(err); // Reject the promise on error
				},
			});
		});
	}
	
	async mapScriptsGroups(){
		this.scriptGroupOptions = this.scriptsFormGroup.get('scriptsCtrl')!.valueChanges.pipe(
			startWith(''),
			map(value => this._filterGroup(value || '')),
		  );
	}

	/* Galleria Filter */ 
	private _filter2(value: string): string[] {
	  	const filterValue = value.toLowerCase();	
	  	return this.options.filter(option => option.toLowerCase().includes(filterValue));
	}
	
	functionFilter(){
		//this.filteredOptions = this.myControl.valueChanges.pipe(
    	this.filteredOptions = this.forthFormGroup.get('myControl')!.valueChanges.pipe(
			startWith(''),
			map(value => this._filter2(value || '')),
			);
	}

	getListaGalleria() {
		const endpoint = "getGallerieList";
		this.apiService.get(environment.api+"/"+endpoint).subscribe({			
			next: (res:any) => {
			this.listaGallerie = res;	
			this.options = res[0].items;
			//console.log(">", this.options)		
			},
			error: (err) => {
			console.error('Error:', err);
			}
		});
	}

	async initializeListaGallerie(){
		await this.getListaGalleria();
		this.functionFilter();
	}

	/* Script Filter */ 
	scriptGroupOptions!: Observable<any>;
	private _filterGroup(value: string):any {
		if (value) {
		  return this.scriptsList
			.map((group: any) => ({name: group.name, includedScripts: _filter(group.includedScripts, value)}))
			.filter((group: any) => group.includedScripts.length > 0);
		}
		return this.scriptsList;
	}

	

	currentValue: string = '';
	response: string = '';
	response1: string = '';

	clientId: string | null = null;
	endFlag:boolean = false;
	hideProgressBar:boolean = true;
	currValue:number = 0;

	savedFiles: File[] = [];
	
	testData = JSON.stringify({"name": "Test", "data": [{"item": "item0"}, {"item": "item1"}]});

	postResponse: string = '';
	postId = "";

	selectedScript: string = "";
	selectedDatabase: string = "";
	selectedCollection: string = "";
	stepOneFlag: boolean = false;
	stepTwoFlag: boolean = false;
	stepThreeFlag: boolean = false;
	stepFourFlag: boolean = false;

	valStep1: any = {valore: "", default: "Step 1: seleziona script", abilitato: true};
	valStep2: any = {valore: "", default: "Step 2: seleziona database", abilitato: false};
	valStep3: any = {valore: "", default: "Step 3: seleziona collection", abilitato: false};
	valStep4: any = {valore: "", default: "Step 4: Nome galleria / file upload", abilitato: false};


	clearAll(){
		this.disableTirthFormGroupFlag  = false;
		this.choicesMade  = {}
		this.submissionData = {};		
		this.isRunning = false;	 
		this.hideMainOutput = true;	
		this.cardModeAggiungi = true; //04/03/26
		this.outputDiv = "";
		this.templateFile = "";
		this.socketStart();
		this.getScriptTutorial("default");
		this.testLink = []
	}


	getScriptStatus() {
		const endpoint = "getScriptStatus";
		const currentClientId = (this.clientID);
		//console.log("currentClientId: ", this.clientID)
		this.apiService.get(environment.api+"/"+endpoint+"/"+ this.clientID, { responseType: 'text' }).subscribe({			
			next: (res) => {
				console.log(res);
			},
			error: (err) => {
			console.error('Error:', err);
			this.response = 'Failed to run test';
			}
		});
		
	}

	
	resizeTextArea(event: Event): void {
		const textarea = event.target as HTMLTextAreaElement;
		if(textarea.id == "mainInputAreaAi"){
			const minRows = 3;
			const maxRows = 8;
			userPromptResize(minRows, maxRows, textarea);
		}
		if(textarea.id == "mainOutputAreaAi"){
			const minRows = 10;
			const maxRows = 35;
			userPromptResize(minRows, maxRows, textarea);
		}
	}
	


	handleFiles(files: File[]) {
		this.savedFiles = files; 
		const fileNames = files.map(file => file.name);
		console.log("File Names:", fileNames);
	}

	
	dbBoundnames(){	
		/* TROVARE METODO PER VALORI DINAMICI */	
		var temp_script = this.scriptsFormGroup.value.scriptsCtrl;
		var temp_db = this.secondFormGroup.value.database;
		var temp_collection = this.tirthFormGroup.value.collection;

		if(!temp_collection && temp_script === "Scarico automatico da DragonFly"){
			temp_collection = "scada";
		}
		if(!temp_collection && temp_script === "Scarico profili e device smartscada"){
			temp_collection = "smartscada";
		}
		const reqData = {db: temp_db, collection: temp_collection}
		console.log("eventData", reqData)
		//getSpecificListaGallerie
		const endpoint = "getSpecificListaGallerie";
		this.apiService.post<any>(`${environment.api}/${endpoint}`, reqData).subscribe({
			next: (res) => {
			//this.postResponse = res;
			this.listaGallerie = res["message"];
			console.log('POST Response:', res["message"]);
			},
			error: (err) => {
			console.error('Error in POST:', err);
			this.postResponse = 'Failed to send data';
			}
		});
	}
		
}


function userPromptResize(minRows:any, maxRows:any, textboxId: HTMLTextAreaElement): void {

	// Get the text content and the number of columns of the text area
	const text: string = textboxId.value;
	const cols: number = textboxId.cols;

	// Split the text into lines and determine the initial row count
	const lines: string[] = text.split('\n');
	let rows: number = lines.length;

	// Ensure the minimum number of rows
	if (rows < minRows) {
		rows = minRows;
	}

	// Calculate additional rows based on content length and column width
	for (let i = 0; i < lines.length; i++) {
		rows += Math.floor(lines[i].length / cols);
	}
	// Set the rows property of the textarea, ensuring it doesn't exceed maxRows
	textboxId.rows = Math.min(rows, maxRows);
}