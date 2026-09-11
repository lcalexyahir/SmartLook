// web/src/app/modules/store/pages/branch-management/branch-management.component.ts
//
// Archivo YA EXISTENTE. Se agrega edición y eliminación (antes
// onSubmit() solo llamaba a createBranch(), nunca a updateBranch()
// aunque el servicio ya lo tenía).

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
  editandoId: number | null = null;
  errorMessage: string | null = null;

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

  nuevaSucursal(): void {
    this.editandoId = null;
    this.errorMessage = null;
    this.branchForm.reset();
    this.showForm = true;
  }

  editarSucursal(branch: any): void {
    this.editandoId = branch.id_sucursal;
    this.errorMessage = null;
    this.branchForm.patchValue({
      id_ciudad: branch.ciudad?.id_ciudad,
      nombre: branch.nombre,
      direccion: branch.direccion,
      telefono: branch.telefono,
      fecha_apertura: branch.fecha_apertura
    });
    this.showForm = true;
  }

  cancelar(): void {
    this.showForm = false;
    this.editandoId = null;
    this.errorMessage = null;
    this.branchForm.reset();
  }

  onSubmit(): void {
    if (this.branchForm.invalid) return;
    this.errorMessage = null;

    const peticion = this.editandoId
      ? this.branchService.updateBranch(this.editandoId, this.branchForm.value)
      : this.branchService.createBranch(this.branchForm.value);

    peticion.subscribe({
      next: () => {
        this.cancelar();
        this.loadData();
      },
      error: (err) => {
        this.errorMessage = err.error?.nombre?.[0]
          || err.error?.id_ciudad?.[0]
          || 'No se pudo guardar la sucursal.';
      }
    });
  }

  eliminarSucursal(branch: any): void {
    if (!confirm(`¿Eliminar la sucursal "${branch.nombre}"?`)) return;
    this.branchService.deleteBranch(branch.id_sucursal).subscribe({
      next: () => this.loadData(),
      error: () => this.errorMessage = 'No se pudo eliminar la sucursal.'
    });
  }
}