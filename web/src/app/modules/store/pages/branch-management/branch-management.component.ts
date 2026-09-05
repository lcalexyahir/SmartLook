import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { BranchService } from '../../services/branch.service';
import { Country, City, Branch } from '../../../../core/models/branch.interface';

@Component({
  selector: 'app-branch-management',
  templateUrl: './branch-management.component.html',
  styleUrls: ['./branch-management.component.scss']
})
export class BranchManagementComponent implements OnInit {
  countries: Country[] = [];
  cities: City[] = [];
  branches: Branch[] = [];
  branchForm!: FormGroup;
  loading = false;
  showForm = false;

  constructor(
    private branchService: BranchService,
    private fb: FormBuilder
  ) {}

  ngOnInit(): void {
    this.initForm();
    this.loadData();
  }

  initForm(): void {
    this.branchForm = this.fb.group({
      id_ciudad: ['', Validators.required],
      nombre: ['', Validators.required],
      direccion: ['', Validators.required],
      telefono: [''],
      fecha_apertura: ['']
    });
  }

  loadData(): void {
    this.loading = true;
    this.branchService.getCountries().subscribe({
      next: (data: any) => this.countries = data.results || data,
      error: () => this.countries = []
    });
    this.branchService.getCities().subscribe({
      next: (data: any) => this.cities = data.results || data,
      error: () => this.cities = []
    });
    this.branchService.getBranches().subscribe({
      next: (data: any) => {
        this.branches = data.results || data;
        this.loading = false;
      },
      error: () => {
        this.branches = [];
        this.loading = false;
      }
    });
  }

  onSubmit(): void {
    if (this.branchForm.invalid) return;

    this.branchService.createBranch(this.branchForm.value).subscribe({
      next: () => {
        this.showForm = false;
        this.branchForm.reset();
        this.loadData();
      },
      error: () => {}
    });
  }
}