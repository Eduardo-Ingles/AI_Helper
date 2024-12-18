import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UploadsFolderComponent } from './uploads-folder.component';

describe('UploadsFolderComponent', () => {
  let component: UploadsFolderComponent;
  let fixture: ComponentFixture<UploadsFolderComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UploadsFolderComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(UploadsFolderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
