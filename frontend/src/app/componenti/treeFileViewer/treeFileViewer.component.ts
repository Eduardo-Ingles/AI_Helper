import {ChangeDetectionStrategy, Component, Input, Output, EventEmitter} from '@angular/core';
import {MatTreeModule} from '@angular/material/tree';
import {MatIconModule} from '@angular/material/icon';
import {MatButtonModule} from '@angular/material/button';
import { CommonModule } from '@angular/common';

import { environment } from '../../../enviroments/environment';

interface FileNode {
    name: string;
    type: 'file' | 'directory';
    children?: FileNode[];
    path?: string; // Full path for files
}

@Component({
    standalone: true,
    selector: 'app-file-tree',
    templateUrl: './treeFileViewer.component.html',
    styleUrl: './treeFileViewer.component.css',
    imports: [MatTreeModule, MatButtonModule, MatIconModule, CommonModule],
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FileTreeComponent {    
    @Output() fileDownload = new EventEmitter<FileNode>();
    @Input() dataSource: FileNode[] = [];
  
    childrenAccessor = (node: FileNode) => node.children ?? [];  
    hasChild = (_: number, node: FileNode) => !!node.children && node.children.length > 0;

    onFileDownload(node: FileNode) {
        if (node.type === 'file') {
            this.fileDownload.emit(node);
        }
    }
    
}