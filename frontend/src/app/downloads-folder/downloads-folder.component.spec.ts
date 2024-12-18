import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DownloadsFolderComponent } from './downloads-folder.component';

describe('DownloadsFolderComponent', () => {
  let component: DownloadsFolderComponent;
  let fixture: ComponentFixture<DownloadsFolderComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DownloadsFolderComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DownloadsFolderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
