import {ChangeDetectionStrategy, Component, signal, Input, booleanAttribute} from '@angular/core';
import {MatButtonToggleModule} from '@angular/material/button-toggle';
import {MatCheckboxModule} from '@angular/material/checkbox';
import { CommonModule } from '@angular/common';
import {MatTooltipModule} from '@angular/material/tooltip';

interface GroupItem {
    checked: boolean;
    name: string;
    visible: boolean;
    enable: boolean;
    tooltip: string;
}

interface ExcludeGroup {
    name: string;
    items: string[];
    any: boolean;
}

@Component({
    selector: 'multi-toggle-mode-button',
    templateUrl: 'customMultiToggler.component.html',
    styleUrl:"customMultiToggler.component.css",
    standalone: true,
    imports: [
        MatButtonToggleModule, 
        MatCheckboxModule, 
        CommonModule, 
        MatTooltipModule
    ],
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MultiButtonToggleMode {
        

    @Input() globalHide:boolean = false;
    @Input() groups: GroupItem[] = []
    //@Input() clientId: string | null = null;

    excludePairs: ExcludeGroup[] = [
        {name: "Profili", items: ["Dispositivi", "Dragonfly", "SmartScada"], any : false},
        {name: "Dispositivi", items: ["Profili", "Dragonfly", "SmartScada"], any : false},
        {name: "Dragonfly", items: ["Profili", "Dispositivi", "SmartScada"], any : false},
        {name: "SmartScada", items: ["Profili", "Dispositivi", "Dragonfly"], any : false},
        {name: "Quality", items: ["Produzione"], any : true},
        {name: "Produzione", items: ["Quality"], any : true},
        {name: "Scarico", items: ["Carico"], any : true},
        {name: "Carico", items: ["Scarico"], any : true},
    ];

    ngOnInit(): void {
        this.handleStartupToggle();
	}

    handleStartupToggle(){

    }
    
    handleToggle_(selectedGroup: GroupItem): void {
        //this.handleToggles(selectedGroup)
        // Toggle the selected group's checked state
        selectedGroup.checked = !selectedGroup.checked;
        
        const scaricoGroup = this.groups.find(group => group.name === 'Scarico');
        const caricoGroup = this.groups.find(group => group.name === 'Carico'); 

        const qualityGroup = this.groups.find(group => group.name === 'Quality');
        const produzioneGroup = this.groups.find(group => group.name === 'Produzione');         
        const profiliGroup = this.groups.find(group => group.name === 'Dispositivi');       
        const dispositiviGroup = this.groups.find(group => group.name === 'Profili');
        const scadaGroup = this.groups.find(group => group.name === 'SmartScada');
        const smartscadadGroup = this.groups.find(group => group.name === 'Dragonfly');
    
        if((profiliGroup && profiliGroup.checked === false) && (dispositiviGroup && dispositiviGroup.checked === false) &&
            (scadaGroup && scadaGroup.checked === false) && (smartscadadGroup && smartscadadGroup.checked === false)
            ){
                profiliGroup.enable = true;
                dispositiviGroup.enable = true;
                scadaGroup.enable = true;
                smartscadadGroup.enable = true;
        }
        
        if (selectedGroup.name === 'Scarico' && selectedGroup.checked) {// If Produzione --> deseleziona Quality
            if (caricoGroup) {
                caricoGroup.checked = false; 
            }  
        } else if (selectedGroup.name === 'Carico' && selectedGroup.checked) { // If Quality --> deseleziona Produzione
            if (scaricoGroup) {
                scaricoGroup.checked = false;
            }            
        }

        // Apply the business rules
        if (selectedGroup.name === 'Produzione' && selectedGroup.checked) {// If Produzione --> deseleziona Quality
            if (qualityGroup) {
                qualityGroup.checked = false; 
            }  
        } else if (selectedGroup.name === 'Quality' && selectedGroup.checked) { // If Quality --> deseleziona Produzione
            if (produzioneGroup) {
                produzioneGroup.checked = false;
            }            
        }
                if (selectedGroup.name === 'Profili' && selectedGroup.checked) {// If Profili --> deseleziona Dispositivi   
            if (profiliGroup) {
                profiliGroup.checked = false;
            }
            if (scadaGroup) {
                scadaGroup.checked = false;
                //scadaGroup.enable = false;
            }
            if (smartscadadGroup) {
                smartscadadGroup.checked = false;
                //smartscadadGroup.enable = false;
            }
        } else if (selectedGroup.name === 'Dispositivi' && selectedGroup.checked) { // If Dispositivi --> deseleziona Profili    
            if (dispositiviGroup) {
                dispositiviGroup.checked = false;
            }
            if (scadaGroup) {
                scadaGroup.checked = false;
                //scadaGroup.enable = false;
            }
            if (smartscadadGroup) {
                smartscadadGroup.checked = false;
                //smartscadadGroup.enable = false;
            }
        }
        if (selectedGroup.name === 'Dragonfly' && selectedGroup.checked) {// If Scada --> deseleziona SmartScada      
            if (scadaGroup) {
                scadaGroup.checked = false;
            }
            if (profiliGroup) {
                profiliGroup.checked = false;
                //profiliGroup.enable = false;   
            }
            if (dispositiviGroup) {
                dispositiviGroup.checked = false;
                //dispositiviGroup.enable = false;  
            }
        } else if (selectedGroup.name === 'SmartScada' && selectedGroup.checked) { // If SmartScada --> deseleziona Scada    
            if (smartscadadGroup) {
                smartscadadGroup.checked = false;
            }
            if (profiliGroup) {
                profiliGroup.checked = false;
                //profiliGroup.enable = false;   
            }
            if (dispositiviGroup) {
                dispositiviGroup.checked = false;
                //dispositiviGroup.enable = false;                
            }
        }
        
        if((qualityGroup && qualityGroup.checked === false) && (produzioneGroup && produzioneGroup.checked === false)){
            qualityGroup.checked = true;
        }

        // Force change detection
        this.groups = [...this.groups];
    }

    handleToggle(selectedGroup: GroupItem){
        selectedGroup.checked = !selectedGroup.checked;
        const excludeItems = this.excludePairs.find(excludePairs => excludePairs.name === selectedGroup.name);
        if(excludeItems){
            if(selectedGroup){
                for(let i=0; i<excludeItems.items.length; i++){                    
                    for(let j=0; j<this.groups.length; j++){
                        if(this.groups[j].name === excludeItems.items[i]){
                            if(selectedGroup.checked === true){
                                this.groups[j].checked = false;
                            }else if(excludeItems.any === true){
                                this.groups[j].checked = true;
                            }
                        }
                    }
                }
            }
        }        
        this.groups = [...this.groups];
    }
        
}



