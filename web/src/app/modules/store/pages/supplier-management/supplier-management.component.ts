import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { SupplierService } from '../../services/supplier.service';
import { Supplier } from '../../../../core/models/branch.interface';

@Component({
  selector: 'app-supplier-management',
  templateUrl: './supplier-management.component.html',
  styleUrls: ['./supplier-management.component.scss']
})
export class SupplierManagementComponent implements OnInit {
  suppliers: Supplier[] = [];
  supplierForm!: FormGroup;
  loading = false;
  showForm = false;

  constructor(
    private supplierService: SupplierService,
    private fb: FormBuilder
  ) {}

  ngOnInit(): void {
    this.initForm();
    this.loadSuppliers();
  }

  initForm(): void {
    this.supplierForm = this.fb.group({
      nombre_empresa: ['', Validators.required],
      nombre_contacto: [''],
      telefono: [''],
      correo: ['', Validators.email],
      direccion: ['']
    });
  }

  loadSuppliers(): void {
    this.loading = true;
    this.supplierService.getSuppliers().subscribe({
      next: (data: any) => {
        this.suppliers = data.results || data;
        this.loading = false;
      },
      error: () => {
        this.suppliers = [];
        this.loading = false;
      }
    });
  }

  onSubmit(): void {
    if (this.supplierForm.invalid) return;

    this.supplierService.createSupplier(this.supplierForm.value).subscribe({
      next: () => {
        this.showForm = false;
        this.supplierForm.reset();
        this.loadSuppliers();
      },
      error: () => {}
    });
  }

  deleteSupplier(id: number): void {
    if (confirm('¿Está seguro de eliminar este proveedor?')) {
      this.supplierService.deleteSupplier(id).subscribe({
        next: () => this.loadSuppliers(),
        error: () => {}
      });
    }
  }
}