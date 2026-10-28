// web/src/app/modules/catalog/pages/product-detail/product-detail.component.ts
//
// MODIFICADO (SaaS - A.5): consulta sin conexión. Con conexión, al abrir una
// prenda se descarga la disponibilidad por sucursal de todas sus variantes
// (tallas y colores) para poder consultarla después sin internet; la copia
// la guarda OfflineCacheInterceptor. Sin conexión se avisa cuando la prenda o
// su disponibilidad no se consultaron antes en este dispositivo.
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { CatalogService } from '../../services/catalog.service';
import { InventoryService } from '../../../inventory/services/inventory.service';
import { CartService } from '../../../cart/services/cart.service';
import { ConexionService } from '../../../../core/services/conexion.service';
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
  // NUEVO (A.5): la prenda o su disponibilidad no están guardadas y no hay conexión.
  sinDatosProducto = false;
  sinDatosStock = false;
  // ===== NUEVO: CU14 - Agregar al Carrito =====
  addingToCart = false;
  cartMessage = '';
  // ===== FIN NUEVO =====
  constructor(
    private route: ActivatedRoute,
    private catalogService: CatalogService,
    private inventoryService: InventoryService,
    private cartService: CartService,
    private conexion: ConexionService
  ) {}
  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loadProduct(Number(id));
    }
  }
  loadProduct(id: number): void {
    this.loading = true;
    this.sinDatosProducto = false;
    this.catalogService.getProduct(id).subscribe({
      next: (data: any) => {
        this.product = data;
        if (data.variantes && data.variantes.length > 0) {
          this.selectVariant(data.variantes[0]);
          this.guardarDisponibilidad(data.variantes);
        }
        this.loading = false;
      },
      error: (err) => {
        this.product = null;
        this.loading = false;
        this.sinDatosProducto = this.conexion.esErrorDeRed(err);
      }
    });
  }
  // NUEVO (A.5): con conexión se descarga la disponibilidad de las demás
  // variantes para poder consultarla sin internet (la guarda el interceptor).
  private guardarDisponibilidad(variantes: any[]): void {
    if (!navigator.onLine) {
      return;
    }
    variantes.slice(1).forEach(v => {
      this.inventoryService.getStockItems(v.id_variante).subscribe({ error: () => undefined });
    });
  }
  selectVariant(variant: any): void {
    this.selectedVariant = variant;
    this.cartMessage = '';
    this.loadDisponibilidad(variant.id_variante);
  }
  loadDisponibilidad(varianteId: number): void {
    this.loadingStock = true;
    this.sinDatosStock = false;
    this.stockPorSucursal = [];
    this.inventoryService.getStockItems(varianteId).subscribe({
      next: (data: any) => {
        // La API pagina las listas ({count, next, previous, results}) -
        // mismo patrón que ya usa stock-list.component.ts.
        this.stockPorSucursal = data.results || data;
        this.loadingStock = false;
      },
      error: (err) => {
        this.loadingStock = false;
        this.sinDatosStock = this.conexion.esErrorDeRed(err);
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
        // SaaS: cada tienda tiene su propio carrito.
        this.cartMessage = this.product?.empresa_nombre
          ? `Agregado a tu carrito de ${this.product.empresa_nombre}`
          : 'Agregado al carrito.';
      },
      error: (err) => {
        this.addingToCart = false;
        this.cartMessage = this.conexion.esErrorDeRed(err)
          ? 'Sin conexión: no se puede agregar al carrito ahora. Puedes reservar la prenda sin conexión.'
          : 'No se pudo agregar al carrito. ¿Iniciaste sesión como cliente?';
      }
    });
  }
  // ===== FIN NUEVO =====
}