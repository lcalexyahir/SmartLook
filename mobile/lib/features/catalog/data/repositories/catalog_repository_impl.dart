import '../../domain/entities/product_entity.dart';
import '../../domain/repositories/catalog_repository.dart';
import '../sources/catalog_remote_source.dart';

class CatalogRepositoryImpl implements CatalogRepository {
  final CatalogRemoteSource remoteSource;

  CatalogRepositoryImpl({required this.remoteSource});

  @override
  Future<List<ProductEntity>> getProducts({
    String? categoria,
    String? marca,
    String? talla,
    String? color,
    String? busqueda,
  }) async {
    final data = await remoteSource.getProducts(
      categoria: categoria,
      marca: marca,
      talla: talla,
      color: color,
      busqueda: busqueda,
    );
    final results = data['results'] ?? data;
    return (results as List)
        .map((json) => ProductEntity.fromJson(json))
        .toList();
  }

  @override
  Future<ProductEntity> getProduct(int id) async {
    final data = await remoteSource.getProduct(id);
    return ProductEntity.fromJson(data);
  }

  @override
  Future<List<dynamic>> getCategories() async {
    return await remoteSource.getCategories();
  }

  @override
  Future<List<dynamic>> getBrands() async {
    return await remoteSource.getBrands();
  }

  @override
  Future<List<dynamic>> getSizes() async {
    return await remoteSource.getSizes();
  }

  @override
  Future<List<dynamic>> getColors() async {
    return await remoteSource.getColors();
  }
}