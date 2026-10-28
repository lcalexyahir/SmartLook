// web/src/app/modules/catalog/pages/product-list/product-list.component.ts
//
// MODIFICADO (SaaS - A.5): sin conexión el catálogo se muestra desde la copia
// guardada en el dispositivo (OfflineCacheInterceptor). Si esa búsqueda nunca
// se hizo con conexión, se avisa en lugar de decir que no hay productos.
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { CatalogService } from '../../services/catalog.service';
import { ConexionService } from '../../../../core/services/conexion.service';
import { Product, Category, Brand, Size, Color } from '../../../../core/models/product.interface';
@Component({
  selector: 'app-product-list',
  templateUrl: './product-list.component.html',
  styleUrls: ['./product-list.component.scss']
})
export class ProductListComponent implements OnInit {
  products: Product[] = [];
  categories: Category[] = [];
  brands: Brand[] = [];
  sizes: Size[] = [];
  colors: Color[] = [];
  filterForm!: FormGroup;
  loading = false;
  sinDatosGuardados = false;
  constructor(
    private catalogService: CatalogService,
    private fb: FormBuilder,
    private conexion: ConexionService
  ) {}
  ngOnInit(): void {
    this.initForm();
    this.loadFilters();
    this.loadProducts();
  }
  initForm(): void {
    this.filterForm = this.fb.group({
      categoria: [''],
      marca: [''],
      talla: [''],
      color: [''],
      busqueda: ['']
    });
  }
  loadFilters(): void {
    this.catalogService.getCategories().subscribe({
      next: (data: any) => this.categories = data.results || data,
      error: () => this.categories = []
    });
    this.catalogService.getBrands().subscribe({
      next: (data: any) => this.brands = data.results || data,
      error: () => this.brands = []
    });
    this.catalogService.getSizes().subscribe({
      next: (data: any) => this.sizes = data.results || data,
      error: () => this.sizes = []
    });
    this.catalogService.getColors().subscribe({
      next: (data: any) => this.colors = data.results || data,
      error: () => this.colors = []
    });
  }
  loadProducts(): void {
    this.loading = true;
    this.sinDatosGuardados = false;
    const filters = this.filterForm.value;
    this.catalogService.getProducts(filters).subscribe({
      next: (data: any) => {
        this.products = data.results || data;
        this.loading = false;
      },
      error: (err) => {
        this.products = [];
        this.loading = false;
        this.sinDatosGuardados = this.conexion.esErrorDeRed(err);
      }
    });
  }
  applyFilters(): void {
    this.loadProducts();
  }
  clearFilters(): void {
    this.filterForm.reset();
    this.loadProducts();
  }
}