import sys
import typing
import bpy.types

GenericType = typing.TypeVar("GenericType")


def assign_action(override_context: typing.
                  Union[typing.Dict, 'bpy.types.Context'] = None,
                  execution_context: typing.Union[str, int] = None,
                  undo: typing.Optional[bool] = None):
    ''' Set this pose Action as active Action on the active Object :file: `addons/pose_library/operators.py\:198 <https://developer.blender.org/diffusion/BA/addons/pose_library/operators.py$198>`_

    :type override_context: typing.Union[typing.Dict, 'bpy.types.Context']
    :type execution_context: typing.Union[str, int]
    :type undo: typing.Optional[bool]
    '''

    pass


def bundle_install(override_context: typing.
                   Union[typing.Dict, 'bpy.types.Context'] = None,
                   execution_context: typing.Union[str, int] = None,
                   undo: typing.Optional[bool] = None,
                   *,
                   asset_library_ref: typing.Union[str, int, typing.Any] = '',
                   filepath: typing.Union[str, typing.Any] = "",
                   hide_props_region: typing.Union[bool, typing.Any] = True,
                   check_existing: typing.Union[bool, typing.Any] = True,
                   filter_blender: typing.Union[bool, typing.Any] = True,
                   filter_backup: typing.Union[bool, typing.Any] = False,
                   filter_image: typing.Union[bool, typing.Any] = False,
                   filter_movie: typing.Union[bool, typing.Any] = False,
                   filter_python: typing.Union[bool, typing.Any] = False,
                   filter_font: typing.Union[bool, typing.Any] = False,
                   filter_sound: typing.Union[bool, typing.Any] = False,
                   filter_text: typing.Union[bool, typing.Any] = False,
                   filter_archive: typing.Union[bool, typing.Any] = False,
                   filter_btx: typing.Union[bool, typing.Any] = False,
                   filter_collada: typing.Union[bool, typing.Any] = False,
                   filter_alembic: typing.Union[bool, typing.Any] = False,
                   filter_usd: typing.Union[bool, typing.Any] = False,
                   filter_obj: typing.Union[bool, typing.Any] = False,
                   filter_volume: typing.Union[bool, typing.Any] = False,
                   filter_folder: typing.Union[bool, typing.Any] = True,
                   filter_blenlib: typing.Union[bool, typing.Any] = False,
                   filemode: typing.Optional[typing.Any] = 8,
                   display_type: typing.Optional[typing.Any] = 'DEFAULT',
                   sort_method: typing.Union[str, int, typing.Any] = ''):
    ''' Copy the current .blend file into an Asset Library. Only works on standalone .blend files (i.e. when no other files are referenced)

    :type override_context: typing.Union[typing.Dict, 'bpy.types.Context']
    :type execution_context: typing.Union[str, int]
    :type undo: typing.Optional[bool]
    :param asset_library_ref: asset_library_ref
    :type asset_library_ref: typing.Union[str, int, typing.Any]
    :param filepath: File Path, Path to file
    :type filepath: typing.Union[str, typing.Any]
    :param hide_props_region: Hide Operator Properties, Collapse the region displaying the operator settings
    :type hide_props_region: typing.Union[bool, typing.Any]
    :param check_existing: Check Existing, Check and warn on overwriting existing files
    :type check_existing: typing.Union[bool, typing.Any]
    :param filter_blender: Filter .blend files
    :type filter_blender: typing.Union[bool, typing.Any]
    :param filter_backup: Filter .blend files
    :type filter_backup: typing.Union[bool, typing.Any]
    :param filter_image: Filter image files
    :type filter_image: typing.Union[bool, typing.Any]
    :param filter_movie: Filter movie files
    :type filter_movie: typing.Union[bool, typing.Any]
    :param filter_python: Filter python files
    :type filter_python: typing.Union[bool, typing.Any]
    :param filter_font: Filter font files
    :type filter_font: typing.Union[bool, typing.Any]
    :param filter_sound: Filter sound files
    :type filter_sound: typing.Union[bool, typing.Any]
    :param filter_text: Filter text files
    :type filter_text: typing.Union[bool, typing.Any]
    :param filter_archive: Filter archive files
    :type filter_archive: typing.Union[bool, typing.Any]
    :param filter_btx: Filter btx files
    :type filter_btx: typing.Union[bool, typing.Any]
    :param filter_collada: Filter COLLADA files
    :type filter_collada: typing.Union[bool, typing.Any]
    :param filter_alembic: Filter Alembic files
    :type filter_alembic: typing.Union[bool, typing.Any]
    :param filter_usd: Filter USD files
    :type filter_usd: typing.Union[bool, typing.Any]
    :param filter_obj: Filter OBJ files
    :type filter_obj: typing.Union[bool, typing.Any]
    :param filter_volume: Filter OpenVDB volume files
    :type filter_volume: typing.Union[bool, typing.Any]
    :param filter_folder: Filter folders
    :type filter_folder: typing.Union[bool, typing.Any]
    :param filter_blenlib: Filter Blender IDs
    :type filter_blenlib: typing.Union[bool, typing.Any]
    :param filemode: File Browser Mode, The setting for the file browser mode to load a .blend file, a library or a special file
    :type filemode: typing.Optional[typing.Any]
    :param display_type: Display Type * ``DEFAULT`` Default -- Automatically determine display type for files. * ``LIST_VERTICAL`` Short List -- Display files as short list. * ``LIST_HORIZONTAL`` Long List -- Display files as a detailed list. * ``THUMBNAIL`` Thumbnails -- Display files as thumbnails.
    :type display_type: typing.Optional[typing.Any]
    :param sort_method: File sorting mode
    :type sort_method: typing.Union[str, int, typing.Any]
    '''

    pass


def catalog_delete(override_context: typing.
                   Union[typing.Dict, 'bpy.types.Context'] = None,
                   execution_context: typing.Union[str, int] = None,
                   undo: typing.Optional[bool] = None,
                   *,
                   catalog_id: typing.Union[str, typing.Any] = ""):
    ''' Remove an asset catalog from the asset library (contained assets will not be affected and show up as unassigned)

    :type override_context: typing.Union[typing.Dict, 'bpy.types.Context']
    :type execution_context: typing.Union[str, int]
    :type undo: typing.Optional[bool]
    :param catalog_id: Catalog ID, ID of the catalog to delete
    :type catalog_id: typing.Union[str, typing.Any]
    '''

    pass


def catalog_new(override_context: typing.
                Union[typing.Dict, 'bpy.types.Context'] = None,
                execution_context: typing.Union[str, int] = None,
                undo: typing.Optional[bool] = None,
                *,
                parent_path: typing.Union[str, typing.Any] = ""):
    ''' Create a new catalog to put assets in

    :type override_context: typing.Union[typing.Dict, 'bpy.types.Context']
    :type execution_context: typing.Union[str, int]
    :type undo: typing.Optional[bool]
    :param parent_path: Parent Path, Optional path defining the location to put the new catalog under
    :type parent_path: typing.Union[str, typing.Any]
    '''

    pass


def catalog_redo(override_context: typing.
                 Union[typing.Dict, 'bpy.types.Context'] = None,
                 execution_context: typing.Union[str, int] = None,
                 undo: typing.Optional[bool] = None):
    ''' Redo the last undone edit to the asset catalogs

    :type override_context: typing.Union[typing.Dict, 'bpy.types.Context']
    :type execution_context: typing.Union[str, int]
    :type undo: typing.Optional[bool]
    '''

    pass


def catalog_undo(override_context: typing.
                 Union[typing.Dict, 'bpy.types.Context'] = None,
                 execution_context: typing.Union[str, int] = None,
                 undo: typing.Optional[bool] = None):
    ''' Undo the last edit to the asset catalogs

    :type override_context: typing.Union[typing.Dict, 'bpy.types.Context']
    :type execution_context: typing.Union[str, int]
    :type undo: typing.Optional[bool]
    '''

    pass


def catalog_undo_push(override_context: typing.
                      Union[typing.Dict, 'bpy.types.Context'] = None,
                      execution_context: typing.Union[str, int] = None,
                      undo: typing.Optional[bool] = None):
    ''' Store the current state of the asset catalogs in the undo buffer

    :type override_context: typing.Union[typing.Dict, 'bpy.types.Context']
    :type execution_context: typing.Union[str, int]
    :type undo: typing.Optional[bool]
    '''

    pass


def catalogs_save(override_context: typing.
                  Union[typing.Dict, 'bpy.types.Context'] = None,
                  execution_context: typing.Union[str, int] = None,
                  undo: typing.Optional[bool] = None):
    ''' Make any edits to any catalogs permanent by writing the current set up to the asset library

    :type override_context: typing.Union[typing.Dict, 'bpy.types.Context']
    :type execution_context: typing.Union[str, int]
    :type undo: typing.Optional[bool]
    '''

    pass


def clear(override_context: typing.Union[typing.
                                         Dict, 'bpy.types.Context'] = None,
          execution_context: typing.Union[str, int] = None,
          undo: typing.Optional[bool] = None,
          *,
          set_fake_user: typing.Union[bool, typing.Any] = False):
    ''' Delete all asset metadata and turn the selected asset data-blocks back into normal data-blocks

    :type override_context: typing.Union[typing.Dict, 'bpy.types.Context']
    :type execution_context: typing.Union[str, int]
    :type undo: typing.Optional[bool]
    :param set_fake_user: Set Fake User, Ensure the data-block is saved, even when it is no longer marked as asset
    :type set_fake_user: typing.Union[bool, typing.Any]
    '''

    pass


def library_refresh(override_context: typing.
                    Union[typing.Dict, 'bpy.types.Context'] = None,
                    execution_context: typing.Union[str, int] = None,
                    undo: typing.Optional[bool] = None):
    ''' Reread assets and asset catalogs from the asset library on disk

    :type override_context: typing.Union[typing.Dict, 'bpy.types.Context']
    :type execution_context: typing.Union[str, int]
    :type undo: typing.Optional[bool]
    '''

    pass


def mark(override_context: typing.Union[typing.
                                        Dict, 'bpy.types.Context'] = None,
         execution_context: typing.Union[str, int] = None,
         undo: typing.Optional[bool] = None):
    ''' Enable easier reuse of selected data-blocks through the Asset Browser, with the help of customizable metadata (like previews, descriptions and tags)

    :type override_context: typing.Union[typing.Dict, 'bpy.types.Context']
    :type execution_context: typing.Union[str, int]
    :type undo: typing.Optional[bool]
    '''

    pass


def open_containing_blend_file(
        override_context: typing.Union[typing.
                                       Dict, 'bpy.types.Context'] = None,
        execution_context: typing.Union[str, int] = None,
        undo: typing.Optional[bool] = None):
    ''' Open the blend file that contains the active asset :file: `startup/bl_operators/assets.py\:98 <https://developer.blender.org/diffusion/B/browse/master/release/scripts/startup/bl_operators/assets.py$98>`_

    :type override_context: typing.Union[typing.Dict, 'bpy.types.Context']
    :type execution_context: typing.Union[str, int]
    :type undo: typing.Optional[bool]
    '''

    pass


def tag_add(override_context: typing.Union[typing.
                                           Dict, 'bpy.types.Context'] = None,
            execution_context: typing.Union[str, int] = None,
            undo: typing.Optional[bool] = None):
    ''' Add a new keyword tag to the active asset :file: `startup/bl_operators/assets.py\:39 <https://developer.blender.org/diffusion/B/browse/master/release/scripts/startup/bl_operators/assets.py$39>`_

    :type override_context: typing.Union[typing.Dict, 'bpy.types.Context']
    :type execution_context: typing.Union[str, int]
    :type undo: typing.Optional[bool]
    '''

    pass


def tag_remove(override_context: typing.
               Union[typing.Dict, 'bpy.types.Context'] = None,
               execution_context: typing.Union[str, int] = None,
               undo: typing.Optional[bool] = None):
    ''' Remove an existing keyword tag from the active asset :file: `startup/bl_operators/assets.py\:62 <https://developer.blender.org/diffusion/B/browse/master/release/scripts/startup/bl_operators/assets.py$62>`_

    :type override_context: typing.Union[typing.Dict, 'bpy.types.Context']
    :type execution_context: typing.Union[str, int]
    :type undo: typing.Optional[bool]
    '''

    pass
