import { RouterModule, Routes } from '@angular/router';
import { NgModule } from '@angular/core';

import {HomeComponent} from './home/home.component';
import { UploadsFolderComponent } from './uploads-folder/uploads-folder.component';
import { DownloadsFolderComponent } from './downloads-folder/downloads-folder.component';
import { SettingsComponent } from './settings/settings.component';
import { StoricoEsecuzioneComponent } from './storicoEsecuzione/storicoEsecuzione.component';


export const routes: Routes = [    
	{ path: 'uploads-folder', component: UploadsFolderComponent },
	{ path: 'downloads-folder', component: DownloadsFolderComponent },
	{ path: 'settings', component: SettingsComponent },
	{ path: 'storico-processi', component: StoricoEsecuzioneComponent },
	{ path: '', component: HomeComponent, pathMatch: 'full'  },
	{ path: '**', redirectTo: '', pathMatch: 'full' },
	//{ path: "settings/:userId", component: SettingsComponent }
];



@NgModule({
    imports: [RouterModule.forRoot(routes)],
    exports: [RouterModule]
})
export class AppRoutingModule { }

  