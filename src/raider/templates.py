from __future__ import annotations

TEMPL_CMAKELISTS = r"""cmake_minimum_required(VERSION 3.20)
project(@NAME@ LANGUAGES CXX)

set(CMAKE_CXX_STANDARD @CXXSTD@)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_library(@NAME@_lib
    src/main.cpp
)
target_include_directories(@NAME@_lib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)

add_executable(@NAME@ src/main.cpp)
target_link_libraries(@NAME@ PRIVATE @NAME@_lib)

enable_testing()
add_executable(@NAME@_tests tests/test_main.cpp)
target_link_libraries(@NAME@_tests PRIVATE @NAME@_lib)
add_test(NAME @NAME@_tests COMMAND @NAME@_tests)
"""

TEMPL_MAIN = r"""#include <iostream>

int main() {
    std::cout << "Hello raider from @NAME@!\n";
    return 0;
}
"""

TEMPL_TEST = r"""#include <cassert>
#include <iostream>

int main() {
    assert(1 + 1 == 2);
    std::cout << "tests OK\n";
    return 0;
}
"""

TEMPL_PRESETS = r"""{
  "version": 6,
  "cmakeMinimumRequired": { "major": 3, "minor": 20, "patch": 0 },

  "configurePresets": [
    {
      "name": "dev",
      "displayName": "Dev (Ninja, Debug)",
      "generator": "Ninja",
      "binaryDir": "${sourceDir}/build/dev",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Debug",
        "CMAKE_EXPORT_COMPILE_COMMANDS": "ON",
        "CMAKE_TOOLCHAIN_FILE": "${sourceDir}/.tools/vcpkg/scripts/buildsystems/vcpkg.cmake"
      }
    },
    {
      "name": "rel",
      "displayName": "Release (Ninja, Release)",
      "generator": "Ninja",
      "binaryDir": "${sourceDir}/build/rel",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Release",
        "CMAKE_EXPORT_COMPILE_COMMANDS": "ON",
        "CMAKE_TOOLCHAIN_FILE": "${sourceDir}/.tools/vcpkg/scripts/buildsystems/vcpkg.cmake"
      }
    }
  ],

  "buildPresets": [
    { "name": "dev", "configurePreset": "dev" },
    { "name": "rel", "configurePreset": "rel" }
  ],

  "testPresets": [
    { "name": "dev", "configurePreset": "dev" },
    { "name": "rel", "configurePreset": "rel" }
  ]
}
"""

TEMPL_CLANGD = r"""CompileFlags:
  Add: [-Wall, -Wextra, -Wpedantic]
"""

TEMPL_CLANG_TIDY = r"""---
# Enable ALL the things! Except not really
# misc-non-private-member-variables-in-classes: the options don't do anything
# modernize-use-nodiscard: too aggressive, attribute is situationally useful
Checks: "*,\
  -google-readability-todo,\
  -altera-*,\
  -fuchsia-*,\
  fuchsia-multiple-inheritance,\
  -llvm-header-guard,\
  -llvm-include-order,\
  -llvmlibc-*,\
  -modernize-use-nodiscard,\
  -misc-non-private-member-variables-in-classes"
HeaderFilterRegex: '^(src|include|tests)/'
WarningsAsErrors: ''
CheckOptions:
  - key: 'bugprone-argument-comment.StrictMode'
    value: 'true'
# Prefer using enum classes with 2 values for parameters instead of bools
  - key: 'bugprone-argument-comment.CommentBoolLiterals'
    value: 'true'
  - key: 'bugprone-misplaced-widening-cast.CheckImplicitCasts'
    value: 'true'
  - key: 'bugprone-sizeof-expression.WarnOnSizeOfIntegerExpression'
    value: 'true'
  - key: 'bugprone-suspicious-string-compare.WarnOnLogicalNotComparison'
    value: 'true'
  - key: 'readability-simplify-boolean-expr.ChainedConditionalReturn'
    value: 'true'
  - key: 'readability-simplify-boolean-expr.ChainedConditionalAssignment'
    value: 'true'
  - key: 'readability-uniqueptr-delete-release.PreferResetCall'
    value: 'true'
  - key: 'cppcoreguidelines-init-variables.MathHeader'
    value: '<cmath>'
  - key: 'cppcoreguidelines-narrowing-conversions.PedanticMode'
    value: 'true'
  - key: 'readability-else-after-return.WarnOnUnfixable'
    value: 'true'
  - key: 'readability-else-after-return.WarnOnConditionVariables'
    value: 'true'
  - key: 'readability-inconsistent-declaration-parameter-name.Strict'
    value: 'true'
  - key: 'readability-qualified-auto.AddConstToQualified'
    value: 'true'
  - key: 'readability-redundant-access-specifiers.CheckFirstDeclaration'
    value: 'true'
# These seem to be the most common identifier styles
  - key: 'readability-identifier-naming.AbstractClassCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.ClassCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.ClassConstantCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.ClassMemberCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.ClassMethodCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.ConstantCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.ConstantMemberCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.ConstantParameterCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.ConstantPointerParameterCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.ConstexprFunctionCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.ConstexprMethodCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.ConstexprVariableCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.EnumCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.EnumConstantCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.FunctionCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.GlobalConstantCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.GlobalConstantPointerCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.GlobalFunctionCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.GlobalPointerCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.GlobalVariableCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.InlineNamespaceCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.LocalConstantCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.LocalConstantPointerCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.LocalPointerCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.LocalVariableCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.MacroDefinitionCase'
    value: 'UPPER_CASE'
  - key: 'readability-identifier-naming.MemberCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.MethodCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.NamespaceCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.ParameterCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.ParameterPackCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.PointerParameterCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.PrivateMemberCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.PrivateMemberPrefix'
    value: 'm_'
  - key: 'readability-identifier-naming.PrivateMethodCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.ProtectedMemberCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.ProtectedMemberPrefix'
    value: 'm_'
  - key: 'readability-identifier-naming.ProtectedMethodCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.PublicMemberCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.PublicMethodCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.ScopedEnumConstantCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.StaticConstantCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.StaticVariableCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.StructCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.TemplateParameterCase'
    value: 'CamelCase'
  - key: 'readability-identifier-naming.TemplateTemplateParameterCase'
    value: 'CamelCase'
  - key: 'readability-identifier-naming.TypeAliasCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.TypedefCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.TypeTemplateParameterCase'
    value: 'CamelCase'
  - key: 'readability-identifier-naming.UnionCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.ValueTemplateParameterCase'
    value: 'CamelCase'
  - key: 'readability-identifier-naming.VariableCase'
    value: 'lower_case'
  - key: 'readability-identifier-naming.VirtualMethodCase'
    value: 'lower_case'
...
"""

TEMPL_CLANG_FORMAT = r"""---
Language: Cpp
AccessModifierOffset: -4
AlignAfterOpenBracket: Align
AlignArrayOfStructures: Left
AlignConsecutiveAssignments:
  Enabled: true
  AcrossEmptyLines: false
  AcrossComments: false
  AlignCompound: false
  AlignFunctionPointers: true
  PadOperators: true
AlignConsecutiveBitFields:
  Enabled: true
  AcrossEmptyLines: false
  AcrossComments: false
  AlignCompound: false
  AlignFunctionPointers: true
  PadOperators: true
AlignConsecutiveDeclarations:
  Enabled: true
  AcrossEmptyLines: false
  AcrossComments: false
  AlignCompound: false
  AlignFunctionPointers: true
  PadOperators: true
AlignConsecutiveMacros:
  Enabled: true
  AcrossEmptyLines: false
  AcrossComments: false
  AlignCompound: false
  AlignFunctionPointers: true
  PadOperators: true
AlignConsecutiveShortCaseStatements:
  Enabled: false
  AcrossEmptyLines: false
  AcrossComments: false
  AlignCaseColons: false
AlignEscapedNewlines: DontAlign
AlignOperands: DontAlign
AlignTrailingComments: Always
AllowAllArgumentsOnNextLine: true
AllowAllParametersOfDeclarationOnNextLine: true
AllowBreakBeforeNoexceptSpecifier: OnlyWithParen
AllowShortBlocksOnASingleLine: Empty
AllowShortCaseLabelsOnASingleLine: false
AllowShortCompoundRequirementOnASingleLine: true
AllowShortEnumsOnASingleLine: false
AllowShortFunctionsOnASingleLine: Inline
AllowShortIfStatementsOnASingleLine: Never
AllowShortLambdasOnASingleLine: All
AllowShortLoopsOnASingleLine: false
AlwaysBreakAfterDefinitionReturnType: None
AlwaysBreakAfterReturnType: None
AlwaysBreakBeforeMultilineStrings: true
AlwaysBreakTemplateDeclarations: Yes
AttributeMacros:
  - __capability
BinPackArguments: false
BinPackParameters: false
BitFieldColonSpacing: Both
BraceWrapping:
  AfterCaseLabel: false
  AfterClass: true
  AfterControlStatement: MultiLine
  AfterEnum: true
  AfterExternBlock: true
  AfterFunction: true
  AfterNamespace: true
  AfterObjCDeclaration: false
  AfterStruct: true
  AfterUnion: true
  BeforeCatch: false
  BeforeElse: false
  BeforeLambdaBody: true
  BeforeWhile: false
  IndentBraces: false
  SplitEmptyFunction: true
  SplitEmptyRecord: true
  SplitEmptyNamespace: true
BreakAdjacentStringLiterals: false
BreakAfterAttributes: Leave
BreakAfterJavaFieldAnnotations: true
BreakArrays: true
BreakBeforeBinaryOperators: NonAssignment
BreakBeforeConceptDeclarations: Always
BreakBeforeBraces: Custom
BreakBeforeInlineASMColon: OnlyMultiline
BreakBeforeTernaryOperators: true
BreakConstructorInitializers: BeforeComma
BreakInheritanceList: BeforeComma
BreakStringLiterals: true
ColumnLimit: 120
CommentPragmas: '^ IWYU pragma:'
CompactNamespaces: false
ConstructorInitializerIndentWidth: 4
ContinuationIndentWidth: 4
Cpp11BracedListStyle: true
DerivePointerAlignment: false
DisableFormat: false
EmptyLineAfterAccessModifier: Never
EmptyLineBeforeAccessModifier: LogicalBlock
ExperimentalAutoDetectBinPacking: false
FixNamespaceComments: true
ForEachMacros:
  - foreach
  - Q_FOREACH
  - BOOST_FOREACH
IfMacros:
  - KJ_IF_MAYBE
IncludeBlocks: Regroup
IncludeCategories:
  # Standard library headers come before anything else
  - Regex: '^<[a-z_]+>'
    Priority: -1
    SortPriority: 0
    CaseSensitive: false
  - Regex: '^<.+\.h(pp)?>'
    Priority: 1
    SortPriority: 0
    CaseSensitive: false
  - Regex: '^<.*'
    Priority: 2
    SortPriority: 0
    CaseSensitive: false
  - Regex: '.*'
    Priority: 3
    SortPriority: 0
    CaseSensitive: false
IncludeIsMainRegex: ''
IncludeIsMainSourceRegex: ''
IndentAccessModifiers: false
IndentCaseBlocks: false
IndentCaseLabels: true
IndentExternBlock: NoIndent
IndentGotoLabels: true
IndentPPDirectives: AfterHash
IndentRequiresClause: true
IndentWidth: 4
IndentWrappedFunctionNames: false
InsertBraces: true
InsertNewlineAtEOF: true
InsertTrailingCommas: Wrapped
IntegerLiteralSeparator:
  Binary: 0
  BinaryMinDigits: 0
  Decimal: 0
  DecimalMinDigits: 0
  Hex: 0
  HexMinDigits: 0
JavaScriptQuotes: Double
JavaScriptWrapImports: true
KeepEmptyLinesAtTheStartOfBlocks: false
KeepEmptyLinesAtEOF: false
LambdaBodyIndentation: Signature
LineEnding: LF
MacroBlockBegin: ''
MacroBlockEnd: ''
MaxEmptyLinesToKeep: 1
NamespaceIndentation: None
ObjCBinPackProtocolList: Never
ObjCBlockIndentWidth: 2
ObjCBreakBeforeNestedBlockParam: true
ObjCSpaceAfterProperty: false
ObjCSpaceBeforeProtocolList: true
PackConstructorInitializers: Never
PenaltyBreakAssignment: 2
PenaltyBreakBeforeFirstCallParameter: 1
PenaltyBreakComment: 300
PenaltyBreakFirstLessLess: 120
PenaltyBreakOpenParenthesis: 0
PenaltyBreakScopeResolution: 500
PenaltyBreakString: 1000
PenaltyBreakTemplateDeclaration: 10
PenaltyExcessCharacter: 1000000
PenaltyIndentedWhitespace: 0
PenaltyReturnTypeOnItsOwnLine: 200
PointerAlignment: Right
PPIndentWidth: -1
QualifierAlignment: Leave
RawStringFormats:
  - Language: Cpp
    Delimiters:
      - cc
      - CC
      - cpp
      - Cpp
      - CPP
      - 'c++'
      - 'C++'
    CanonicalDelimiter: ''
    BasedOnStyle: google
  - Language: TextProto
    Delimiters:
      - pb
      - PB
      - proto
      - PROTO
    EnclosingFunctions:
      - EqualsProto
      - EquivToProto
      - PARSE_PARTIAL_TEXT_PROTO
      - PARSE_TEST_PROTO
      - PARSE_TEXT_PROTO
      - ParseTextOrDie
      - ParseTextProtoOrDie
      - ParseTestProto
      - ParsePartialTestProto
    CanonicalDelimiter: ''
    BasedOnStyle: google
ReferenceAlignment: Pointer
ReflowComments: true
RemoveBracesLLVM: false
RemoveParentheses: Leave
RemoveSemicolon: false
RequiresClausePosition: OwnLine
RequiresExpressionIndentation: OuterScope
SeparateDefinitionBlocks: Always
ShortNamespaceLines: 1
SkipMacroDefinitionBody: false
SortIncludes: CaseSensitive
SortJavaStaticImport: Before
SortUsingDeclarations: LexicographicNumeric
SpaceAfterCStyleCast: false
SpaceAfterLogicalNot: false
SpaceAfterTemplateKeyword: false
SpaceAroundPointerQualifiers: Default
SpaceBeforeAssignmentOperators: true
SpaceBeforeCaseColon: false
SpaceBeforeCpp11BracedList: true
SpaceBeforeCtorInitializerColon: true
SpaceBeforeInheritanceColon: true
SpaceBeforeJsonColon: false
SpaceBeforeParens: ControlStatementsExceptControlMacros
SpaceBeforeParensOptions:
  AfterControlStatements: true
  AfterForeachMacros: false
  AfterFunctionDefinitionName: false
  AfterFunctionDeclarationName: false
  AfterIfMacros: false
  AfterOverloadedOperator: false
  AfterPlacementOperator: true
  AfterRequiresInClause: false
  AfterRequiresInExpression: false
  BeforeNonEmptyParentheses: false
SpaceBeforeRangeBasedForLoopColon: true
SpaceBeforeSquareBrackets: false
SpaceInEmptyBlock: false
SpacesBeforeTrailingComments: 2
SpacesInAngles: Never
SpacesInContainerLiterals: false
SpacesInLineCommentPrefix:
  Minimum: 1
  Maximum: -1
SpacesInParens: Never
SpacesInParensOptions:
  InCStyleCasts: false
  InConditionalStatements: false
  InEmptyParentheses: false
  Other: false
SpacesInSquareBrackets: false
Standard: Auto
StatementAttributeLikeMacros:
  - Q_EMIT
StatementMacros:
  - Q_UNUSED
  - QT_REQUIRE_VERSION
TabWidth: 4
UseTab: Never
VerilogBreakBetweenInstancePorts: true
WhitespaceSensitiveMacros:
  - STRINGIZE
  - PP_STRINGIZE
  - BOOST_PP_STRINGIZE
...
"""

TEMPL_VCPKG = r"""{
  "name": "@NAME@",
  "version-string": "0.1.0",
  "dependencies": []
}
"""
