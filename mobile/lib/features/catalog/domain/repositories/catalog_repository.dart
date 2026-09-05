import '../entities/product_entity.dart';

abstract class CatalogRepository {
  Future<List<ProductEntity>> getProducts({
    String? categoria,
    String? marca,
    String? talla,
    String? color,
    String? busqueda,
  });

  Future<ProductEntity> getProduct(int id);

  Future<List<dynamic>> getCategories();
  Future<List<dynamic>> getBrands();
  Future<List<dynamic>> getSizes();
  Future<List<dynamic>> getColors();
}