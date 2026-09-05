import { Component, OnInit } from '@angular/core';
import { InventoryService } from '../../services/inventory.service';
import { StockItem } from '../../../../core/models/inventory.interface';

@Component({
  selector: 'app-stock-list',
  templateUrl: './stock-list.component.html',
  styleUrls: ['./stock-list.component.scss']
})
export class StockListComponent implements OnInit {
  stockItems: StockItem[] = [];
  loading = false;

  constructor(private inventoryService: InventoryService) {}

  ngOnInit(): void {
    this.loadStock();
  }

  loadStock(): void {
    this.loading = true;
    this.inventoryService.getStockItems().subscribe({
      next: (data: any) => {
        this.stockItems = data.results || data;
        this.loading = false;
      },
      error: () => {
        this.stockItems = [];
        this.loading = false;
      }
    });
  }
}