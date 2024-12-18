import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';

import { AppComponent } from './app.component';
import { AppRoutingModule } from './app.routes';
import { ApiTest } from './api.service';
import { HomeComponent } from './home/home.component';

import { DataService } from './data.service';
import { WebSocketService } from './websocket.service';
import {WebSocketClientComponent } from './home/wsComponent.component';

import {FileUploaderComponent} from "./componenti/file-uploader/file-uploader.component";
import { CommonModule } from '@angular/common';
import {CustomAutocomplete} from "./componenti/customAutocompleteTreeView/customautoCompleteTreeView.component";

import {TableDynamicArrayDataExample} from "./componenti/dynamicTable/dynamicTable.component";


@NgModule({
	declarations: [AppComponent, HomeComponent, WebSocketClientComponent, FileUploaderComponent],
	imports: [
		BrowserModule,
		FormsModule,
		AppRoutingModule,
		HttpClientModule,
		CommonModule
	],
	providers: [ApiTest, DataService, WebSocketService ],
	bootstrap: [AppComponent]
})
export class AppModule {}
