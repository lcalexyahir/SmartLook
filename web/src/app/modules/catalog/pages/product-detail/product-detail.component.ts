import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { CatalogService } from '../../services/catalog.service';
import { InventoryService } from '../../../inventory/services/inventory.service';
import { CartService } from '../../../cart/services/cart.service';
import { Product } from '../../../../core/models/product.interface';
import { StockItem } from '../../../../core/models/inventory.interface';

@Component({
  selector: 'app-product-detail',
  templateUrl: './product-detail.component.html',
  styleUrls: ['./product-detail.component.scss']
})
export class ProductDetailComponent implements OnInit {
  product: Product | null = null;
  loading = false;
  selectedVariant: any = null;
  stockPorSucursal: StockItem[] = [];
  loadingStock = false;

  // ===== NUEVO: CU14 - Agregar al Carrito =====
  addingToCart = false;
  cartMessage = '';
  // ===== FIN NUEVO =====

  constructor(
    private route: ActivatedRoute,
    private catalogService: CatalogService,
    private inventoryService: InventoryService,
    private cartService: CartService
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loadProduct(Number(id));
    }
  }

  loadProduct(id: number): void {
    this.loading = true;
    this.catalogService.getProduct(id).subscribe({
      next: (data: any) => {
        this.product = data;
        if (data.variantes && data.variantes.length > 0) {
          this.selectVariant(data.variantes[0]);
        }
        this.loading = false;
      },
      error: () => {
        this.product = null;
        this.loading = false;
      }
    });
  }

  selectVariant(variant: any): void {
    this.selectedVariant = variant;
    this.cartMessage = '';
    this.loadDisponibilidad(variant.id_variante);
  }

  loadDisponibilidad(varianteId: number): void {
    this.loadingStock = true;
    this.stockPorSucursal = [];
    this.inventoryService.getStockItems(varianteId).subscribe({
      next: (data: any) => {
        // La API pagina las listas ({count, next, previous, results}) -
        // mismo patrón que ya usa stock-list.component.ts.
        this.stockPorSucursal = data.results || data;
        this.loadingStock = false;
      },
      error: () => {
        this.loadingStock = false;
      }
    });
  }

  // ===== NUEVO: CU14 - Agregar al Carrito =====
  agregarAlCarrito(): void {
    if (!this.selectedVariant) {
      return;
    }
    this.addingToCart = true;
    this.cartMessage = '';
    this.cartService.agregarItem(this.selectedVariant.id_variante, 1).subscribe({
      next: () => {
        this.addingToCart = false;
        this.cartMessage = 'Agregado al carrito.';
      },
      error: () => {
        this.addingToCart = false;
        this.cartMessage = 'No se pudo agregar al carrito. ¿Iniciaste sesión como cliente?';
      }
    });
  }
  // ===== FIN NUEVO =====
}